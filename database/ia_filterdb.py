import logging
from struct import pack
import re
import base64
from pyrogram.file_id import FileId
from pymongo.errors import DuplicateKeyError, PyMongoError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow.exceptions import ValidationError
from info import DATABASE_URI, DATABASE_NAME, COLLECTION_NAME, USE_CAPTION_FILTER, MAX_B_TN, INDEX_EXTENSIONS
from utils import get_settings, save_group_settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize MongoDB connection
client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]
instance = Instance.from_db(db)

@instance.register
class Media(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True, validate=lambda x: x > 0)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)

    class Meta:
        indexes = ('$file_name', )
        collection_name = COLLECTION_NAME

async def get_all_files():
    """Get all files from database"""
    files = []
    logger.info('Fetching Files...')
    try:
        async for file in Media.find({}):
            files.append(file)
        logger.info('Fetched all Files successfully')
    except PyMongoError as e:
        logger.error(f'Error fetching files: {e}')
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
        logger.exception(f'Validation error saving file: {e}')
        return False, 2
    else:
        try:
            await file.commit()
        except DuplicateKeyError:
            logger.warning(f'{getattr(media, "file_size", "NO_FILE")} already exists in database')
            return False, 0
        except PyMongoError as e:
            logger.error(f'Database error saving file: {e}')
            return False, 2
        else:
            logger.info(f'{getattr(media, "file_size", "NO_FILE")} saved to database')
            return True, 1

async def get_search_results(chat_id, query, file_type=None, max_results=10, offset=0, filter=False, lang=None):
    """For given query return (results, next_offset, total_results)"""
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
        logger.error(f'Invalid regex pattern: {e}')
        return [], '', 0

    filter_query = {'$or': [{'file_name': regex}, {'caption': regex}]} if USE_CAPTION_FILTER else {'file_name': regex}
    
    if file_type:
        filter_query['file_type'] = file_type

    try:
        if lang:
            cursor = Media.find(filter_query)
            lang_files = [
                file async for file in cursor 
                if (file.caption and lang in file.caption.lower()) or 
                   (file.file_name and lang in file.file_name.lower())
            ]
            files = lang_files[offset:][:max_results]
            total_results = len(lang_files)
        else:
            total_results = await Media.count_documents(filter_query)
            cursor = Media.find(filter_query).sort('$natural', -1).skip(offset).limit(max_results)
            files = await cursor.to_list(length=max_results)
        
        next_offset = offset + max_results
        if next_offset >= total_results:
            next_offset = ''
            
        return files, next_offset, total_results
        
    except PyMongoError as e:
        logger.error(f'Database error during search: {e}')
        return [], '', 0

async def get_file_details(query):
    """Get file details by file_id"""
    try:
        filedetails = await Media.find_one({'file_id': query})
        return [filedetails] if filedetails else []
    except PyMongoError as e:
        logger.error(f'Error getting file details: {e}')
        return []

# ... (keep the existing encode_file_id, encode_file_ref, unpack_new_file_id functions)
