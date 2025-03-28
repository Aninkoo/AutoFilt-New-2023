import re
from os import environ
import asyncio
import json
from collections import defaultdict
from typing import Dict, List, Union
from pyrogram import Client
from time import time

id_pattern = re.compile(r'^.\d+$')
def is_enabled(value, default):
    if value.strip().lower() in ["on", "true", "yes", "1", "enable", "y"]:
        return True
    elif value.strip().lower() in ["off", "false", "no", "0", "disable", "n"]:
        return False
    else:
        return default

# Bot information
SESSION = environ.get('SESSION', 'Media_search')
API_ID = int(environ.get('API_ID', '18037664'))
API_HASH = environ.get('API_HASH', '2f30344d1a5d5fefc42241ab6c65d02d')
BOT_TOKEN = environ.get('BOT_TOKEN', '5221907668:AAFTDiAuNMVH2lH72fLZvrmA9dK-ue_f--M')
PORT = environ.get("PORT", "8080")

# Bot settings
CACHE_TIME = int(environ.get('CACHE_TIME', 300))
USE_CAPTION_FILTER = bool(environ.get('USE_CAPTION_FILTER', True))
BOT_START_TIME = time()

# Bot images & videos
PICS = (environ.get('PICS', 'https://telegra.ph/file/6866eb1188bbe61e21411.jpg https://telegra.ph/file/25b5ccb4837abda41818e.jpg https://telegra.ph/file/0582d4846795a617fb62c.jpg')).split()
REQ_PICS = (environ.get('REQ_PICS', 'https://graph.org/file/4bad65318f2f6164a40a3.mp4')).split()
NOR_IMG = environ.get("NOR_IMG", "https://graph.org/file/1f03e7fdc717424b1b7be.jpg")
MELCOW_VID = environ.get("MELCOW_VID", "https://graph.org/file/517dbf019c2490c29d8fa.mp4")
SPELL_IMG = environ.get("SPELL_IMG", "https://telegra.ph/file/2a888a370f479f4338f7c.jpg")

# Admins, Channels & Users
ADMINS = [int(admin) if id_pattern.search(admin) else admin for admin in environ.get('ADMINS', '1392566136').split()]
CHANNELS = [int(ch) if id_pattern.search(ch) else ch for ch in environ.get('CHANNELS', '').split()]
UPDATES_CHNL = int(environ.get('UPDATES_CHNL', '-1002104181305'))
auth_users = [int(user) if id_pattern.search(user) else user for user in environ.get('AUTH_USERS', '').split()]
AUTH_USERS = (auth_users + ADMINS) if auth_users else []
auth_channel = environ.get('AUTH_CHANNEL',"-1001676503062")
auth_grp = environ.get('AUTH_GROUP')
AUTH_CHANNEL = int(auth_channel) if auth_channel and id_pattern.search(auth_channel) else None
AUTH_GROUPS = [int(ch) for ch in auth_grp.split()] if auth_grp else None
support_chat_id = environ.get('SUPPORT_CHAT_ID')
reqst_channel = environ.get('REQST_CHANNEL_ID','')
REQST_CHANNEL = int(reqst_channel) if reqst_channel and id_pattern.search(reqst_channel) else None
SUPPORT_CHAT_ID = -1001987439557
NO_RESULTS_MSG = bool(environ.get("NO_RESULTS_MSG", False))
BIN_CHANNEL = int(environ.get("BIN_CHANNEL", "-1002247764745"))
URL = environ.get("URL", "")

# MongoDB information
DATABASE_URI = environ.get('DATABASE_URI', "mongodb+srv://trial:trial@cluster0.rmcsv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DATABASE_NAME = environ.get('DATABASE_NAME', "Trialdb")
COLLECTION_NAME = environ.get('COLLECTION_NAME', 'FILES')

# Others
DELETE_CHANNELS = [int(dch) if id_pattern.search(dch) else dch for dch in environ.get('DELETE_CHANNELS', '0').split()]
MAX_B_TN = environ.get("MAX_B_TN", "10")
MAX_BTN = is_enabled((environ.get('MAX_BTN', "True")), True)
LOG_CHANNEL = int(environ.get('LOG_CHANNEL', '-1001760665688'))
SUPPORT_CHAT = environ.get('SUPPORT_CHAT', 'isaiminiprime_support')
P_TTI_SHOW_OFF = is_enabled((environ.get('P_TTI_SHOW_OFF', "True")), False)
IMDB = is_enabled((environ.get('IMDB', "False")), True)
AUTO_FFILTER = is_enabled((environ.get('AUTO_FFILTER', "True")), True)
AUTO_DELETE = is_enabled((environ.get('AUTO_DELETE', "True")), True)
SINGLE_BUTTON = is_enabled((environ.get('SINGLE_BUTTON', "False")), True)
CUSTOM_FILE_CAPTION = environ.get("CUSTOM_FILE_CAPTION", '<blockquote><b>FILE : <code>{file_name}</code> \n\nSize : {file_size}</blockquote>\n♨️ 𝐁𝐫𝐨𝐮𝐠𝐡𝐭 𝐓𝐨 𝐘𝐨𝐮 𝐁𝐲:- <a href=https://t.me/isaimini_updates>❤️ 𝗜𝘀𝗮𝗶𝗺𝗶𝗻𝗶 𝗣𝗿𝗶𝗺𝗲 ❤️</a></b>')
BATCH_FILE_CAPTION = environ.get("BATCH_FILE_CAPTION", '<blockquote><b>{file_caption}</b></blockquote>\n<b>♨️ 𝐁𝐫𝐨𝐮𝐠𝐡𝐭 𝐓𝐨 𝐘𝐨𝐮 𝐁𝐲:- <a href=https://t.me/isaimini_updates>❤️ 𝗜𝘀𝗮𝗶𝗺𝗶𝗻𝗶 𝗣𝗿𝗶𝗺𝗲 ❤️</a></b> ')
IMDB_TEMPLATE = environ.get("IMDB_TEMPLATE", '<b>🧿 <u>𝚃𝙸𝚃𝙻𝙴</u> :  {title} \n🌟 <u>𝚁𝙰𝚃𝙸𝙽𝙶</u> : {rating} \n🎭 <u>𝙶𝙴𝙽𝚁𝙴</u> : {genres} \n📆 <u>𝚁𝙴𝙻𝙴𝙰𝚂𝙴</u> : {year} \n⏰ <u>𝙳𝚄𝚁𝙰𝚃𝙸𝙾𝙽</u> : {runtime} \n🎙️<u>𝙻𝙰𝙽𝙶𝚄𝙰𝙶𝙴</u> : {languages} \n🔖 <u>𝚂𝙷𝙾𝚁𝚃</u> : {plot}</b>')
LONG_IMDB_DESCRIPTION = is_enabled(environ.get("LONG_IMDB_DESCRIPTION", "False"), False)
SPELL_CHECK_REPLY = is_enabled(environ.get("SPELL_CHECK_REPLY", "True"), True)
MAX_LIST_ELM = environ.get("MAX_LIST_ELM", None)
INDEX_REQ_CHANNEL = int(environ.get('INDEX_REQ_CHANNEL', LOG_CHANNEL))
INDEX_EXTENSIONS = [extensions.lower() for extensions in environ.get('INDEX_EXTENSIONS', 'mp4 mkv avi').split()]
FILE_STORE_CHANNEL = [int(ch) for ch in (environ.get('FILE_STORE_CHANNEL', '-1002123294045')).split()]
MELCOW_NEW_USERS = is_enabled((environ.get('MELCOW_NEW_USERS', "True")), True)
PROTECT_CONTENT = is_enabled((environ.get('PROTECT_CONTENT', "False")), False)
PUBLIC_FILE_STORE = is_enabled((environ.get('PUBLIC_FILE_STORE', "False")), True)
SHORTLINK_URL = (environ.get("SHORTLINK_URL", "instantearn.in")).split()
SHORTLINK_API = (environ.get("SHORTLINK_API", "85738b1e5dc3dc11333d57b84db5200978d82ec7")).split()
VERIFY_EXPIRE = int(environ.get('VERIFY_EXPIRE', 86400)) # Add time in seconds
IS_VERIFY = is_enabled(environ.get("IS_VERIFY", "False"), False)
DAILY_UPDATE_LINK = environ.get("DAILY_UPDATE_LINK", "https://t.me/isaimini_daily_update")
IS_STREAM = is_enabled((environ.get('IS_STREAM', "True")), True)

LOG_STR = "Current Cusomized Configurations are:-\n"
LOG_STR += ("IMDB Results are enabled, Bot will be showing imdb details for you queries.\n" if IMDB else "IMBD Results are disabled.\n")
LOG_STR += ("P_TTI_SHOW_OFF found , Users will be redirected to send /start to Bot PM instead of sending file file directly\n" if P_TTI_SHOW_OFF else "P_TTI_SHOW_OFF is disabled files will be send in PM, instead of sending start.\n")
LOG_STR += ("SINGLE_BUTTON is Found, filename and files size will be shown in a single button instead of two separate buttons\n" if SINGLE_BUTTON else "SINGLE_BUTTON is disabled , filename and file_sixe will be shown as different buttons\n")
LOG_STR += (f"CUSTOM_FILE_CAPTION enabled with value {CUSTOM_FILE_CAPTION}, your files will be send along with this customized caption.\n" if CUSTOM_FILE_CAPTION else "No CUSTOM_FILE_CAPTION Found, Default captions of file will be used.\n")
LOG_STR += ("Long IMDB storyline enabled." if LONG_IMDB_DESCRIPTION else "LONG_IMDB_DESCRIPTION is disabled , Plot will be shorter.\n")
LOG_STR += ("Spell Check Mode Is Enabled, bot will be suggesting related movies if movie not found\n" if SPELL_CHECK_REPLY else "SPELL_CHECK_REPLY Mode disabled\n")
LOG_STR += (f"MAX_LIST_ELM Found, long list will be shortened to first {MAX_LIST_ELM} elements\n" if MAX_LIST_ELM else "Full List of casts and crew will be shown in imdb template, restrict them by adding a value to MAX_LIST_ELM\n")
LOG_STR += f"Your current IMDB template is {IMDB_TEMPLATE}"
