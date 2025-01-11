import logging
from struct import pack
import re, asyncio
import base64
from pyrogram import Client, filters, enums
from pyrogram.file_id import FileId
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow.exceptions import ValidationError
from info import DATABASE_URI, DATABASE_NAME, COLLECTION_NAME, USE_CAPTION_FILTER, MAX_B_TN, INDEX_EXTENSIONS, ADMINS
from utils import get_settings, save_group_settings
from database.ia_filterdb import Media
from asyncio import Event

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

db_client = AsyncIOMotorClient(DATABASE_URI)
db = db_client[DATABASE_NAME]
instance = Instance.from_db(db)

STOP_EVENT = Event()

@Client.on_message(filters.command("sendfile") & filters.user(ADMINS))
async def sendallfilesindb(client, message):
    args = message.text.split()
    if len(args) != 2:
        return await message.reply_text("Usage: /sendfile Channel_Id")
    
    try:
        target_id = int(args[1])
    except ValueError:
        return await message.reply_text("Invalid Channel ID. Please provide a numeric ID.")
    
    global STOP_EVENT
    STOP_EVENT.clear()
    await message.reply_text("Process Started...")
    logger.info(f'Fetching Files...')
    
    async for file in Media.find({}):
        if STOP_EVENT.is_set():
            return await message.reply_text("File sending process stopped.")
        
        file_id = file.file_id
        file_caption = file.caption
        f_name = file.file_name
        title = file_caption if file_caption else f_name
        
        try:
            await client.send_cached_media(
                chat_id=target_id,
                file_id=file_id,
                caption=title,
                protect_content=False,
            )
        except Exception as e:
            logger.error(f"Error sending file {file_id}: {e}")
        await asyncio.sleep(1)

@Client.on_message(filters.command("stop") & filters.user(ADMINS))
async def stop_sending_files(client, message):
    """Command to stop the file-sending process."""
    global STOP_EVENT
    STOP_EVENT.set()  # Set the stop flag
    await message.reply_text("File sending process will stop shortly.")
