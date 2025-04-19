import logging
from struct import pack
import re
import base64
from pyrogram.file_id import FileId
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow.exceptions import ValidationError
from info import DATABASE_URI, DATABASE_NAME, COLLECTION_NAME, USE_CAPTION_FILTER, MAX_B_TN, INDEX_EXTENSIONS
from utils import get_settings, save_group_settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize MongoDB connection
client = AsyncIOMotorClient(DATABASE_URI, serverSelectionTimeoutMS=5000)
db = client[DATABASE_NAME]
instance = Instance.from_db(db)

# Define fields with explicit marshmallow kwargs
@instance.register
class Media(Document):
    file_id = fields.StringField(attribute='_id', required=True)
    file_ref = fields.StringField(allow_none=True)
    file_name = fields.StringField(required=True)
    file_size = fields.IntegerField(required=True)
    file_type = fields.StringField(allow_none=True)
    mime_type = fields.StringField(allow_none=True)
    caption = fields.StringField(allow_none=True)

    class Meta:
        indexes = ('$file_name', )
        collection_name = COLLECTION_NAME

async def get_all_files():
    files = []
    logger.info('Fetching Files...')
    async for file in Media.find({}):
        files.append(file)
    logger.info('Fetched all Files...')
    return files

async def save_file(media):
    """Save file in database"""
    file_id, file_ref = unpack_new_file_id(media.file_id)
    file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
    try:
        file = Media(
            file_id=file_id,
            file_ref=file_ref,
            file_name=file_name,
            file_size=media.file_size,
            mime_type=media.mime_type,
            caption=file_name,
        )
    except ValidationError as e:
        logger.exception('Error occurred while saving file in database: %s', str(e))
        return False, 2
    else:
        try:
            await file.commit()
        except DuplicateKeyError:
            logger.warning(
                '%s is already saved in database',
                getattr(media, "file_size", "NO_FILE")
            )
            return False, 0
        except Exception as e:
            logger.error('Unexpected error saving file: %s', str(e))
            return False, 2
        else:
            logger.info('%s is saved to database', getattr(media, "file_size", "NO_FILE"))
            return True, 1

async def get_search_results(chat_id, query, file_type=None, max_results=10, offset=0, filter=False, lang=None):
    """For given query return (results, next_offset)"""
    if chat_id is not None:
        settings = await get_settings(int(chat_id))
        max_results = 10 if settings.get('max_btn', False) else int(MAX_B_TN)
    
    query = query.strip()
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_\(\)])' + query + r'(\b|[\.\+\-_\(\)])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_\(\)]')
    
    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except re.error as e:
        logger.error('Regex compilation error: %s', str(e))
        return [], '', 0

    filter_query = {'$or': [{'file_name': regex}, {'caption': regex}]} if USE_CAPTION_FILTER else {'file_name': regex}

    if file_type:
        filter_query['file_type'] = file_type

    try:
        if lang:
            lang_filter = {'$or': [
                {'caption': {'$regex': lang, '$options': 'i'}},
                {'file_name': {'$regex': lang, '$options': 'i'}}
            ]}
            combined_filter = {'$and': [filter_query, lang_filter]}
            
            total_results = await Media.count_documents(combined_filter)
            cursor = Media.find(combined_filter).sort('$natural', -1)
            
            files = await cursor.skip(offset).limit(max_results).to_list(length=max_results)
        else:
            total_results = await Media.count_documents(filter_query)
            cursor = Media.find(filter_query).sort('$natural', -1)
            files = await cursor.skip(offset).limit(max_results).to_list(length=max_results)

        next_offset = offset + max_results
        if next_offset >= total_results:
            next_offset = ''

        return files, next_offset, total_results
    except Exception as e:
        logger.error('Error in get_search_results: %s', str(e))
        return [], '', 0

async def get_bad_files(query, file_type=None, filter=False):
    """For given query return (results, next_offset)"""
    query = query.strip()
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_]')
    
    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except re.error as e:
        logger.error('Regex compilation error: %s', str(e))
        return [], 0

    filter_query = {'$or': [{'file_name': regex}, {'caption': regex}]} if USE_CAPTION_FILTER else {'file_name': regex}

    if file_type:
        filter_query['file_type'] = file_type

    try:
        total_results = await Media.count_documents(filter_query)
        cursor = Media.find(filter_query).sort('$natural', -1)
        files = await cursor.to_list(length=total_results)
        return files, total_results
    except Exception as e:
        logger.error('Error in get_bad_files: %s', str(e))
        return [], 0

async def get_file_details(query):
    try:
        filedetails = await Media.find_one({'file_id': query})
        return [filedetails] if filedetails else []
    except Exception as e:
        logger.error('Error in get_file_details: %s', str(e))
        return []

def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0

    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0
            r += bytes([i])

    return base64.urlsafe_b64encode(r).decode().rstrip("=")

def encode_file_ref(file_ref: bytes) -> str:
    return base64.urlsafe_b64encode(file_ref).decode().rstrip("=")

def unpack_new_file_id(new_file_id):
    """Return file_id, file_ref"""
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )
    file_ref = encode_file_ref(decoded.file_reference)
    return file_id, file_ref
