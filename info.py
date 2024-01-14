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
BOT_TOKEN = environ.get('BOT_TOKEN', '5251712158:AAFEh1_3x5bWNwpeUDwd5cyRuI6Tdz5Qf0o')
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
CHANNELS = [int(ch) if id_pattern.search(ch) else ch for ch in environ.get('CHANNELS', '0').split()]
auth_users = [int(user) if id_pattern.search(user) else user for user in environ.get('AUTH_USERS', '').split()]
AUTH_USERS = (auth_users + ADMINS) if auth_users else []
auth_channel = environ.get('AUTH_CHANNEL',"-1001676503062")
auth_grp = environ.get('AUTH_GROUP')
AUTH_CHANNEL = int(auth_channel) if auth_channel and id_pattern.search(auth_channel) else None
AUTH_GROUPS = [int(ch) for ch in auth_grp.split()] if auth_grp else None
support_chat_id = environ.get('SUPPORT_CHAT_ID')
reqst_channel = environ.get('REQST_CHANNEL_ID','-1001905521512')
REQST_CHANNEL = int(reqst_channel) if reqst_channel and id_pattern.search(reqst_channel) else None
SUPPORT_CHAT_ID = -1001987439557
NO_RESULTS_MSG = bool(environ.get("NO_RESULTS_MSG", False))
BIN_CHANNEL = int(environ.get("BIN_CHANNEL", "-1002044951526"))
URL = environ.get("URL", "https://isaimini-filter-bot-2023-6336c9727a70.herokuapp.com/")

# MongoDB information
DATABASE_URI = environ.get('DATABASE_URI', "mongodb+srv://advfilter:advfilter@cluster0.5dksd.mongodb.net/?retryWrites=true&w=majority")
DATABASE_NAME = environ.get('DATABASE_NAME', "AdvFilterbot")
COLLECTION_NAME = environ.get('COLLECTION_NAME', 'Telegram_files')

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
SINGLE_BUTTON = is_enabled((environ.get('SINGLE_BUTTON', "True")), True)
CUSTOM_FILE_CAPTION = environ.get("CUSTOM_FILE_CAPTION", '<b>©️ Main Channel:-  \n<a href=https://t.me/isaimini_updates>❤️ 𝗜𝘀𝗮𝗶𝗺𝗶𝗻𝗶 𝗣𝗿𝗶𝗺𝗲 ❤️</a></b> \n\n<b>FILE : <code>{file_name}</code> \n\nSize : {file_size}</b>')
BATCH_FILE_CAPTION = environ.get("BATCH_FILE_CAPTION", '<b>{file_caption}</b> \n\n<b>©️ Main Channel:-  \n<a href=https://t.me/isaimini_updates>❤️ 𝗜𝘀𝗮𝗶𝗺𝗶𝗻𝗶 𝗣𝗿𝗶𝗺𝗲 ❤️</a></b>')
IMDB_TEMPLATE = environ.get("IMDB_TEMPLATE", '')
LONG_IMDB_DESCRIPTION = is_enabled(environ.get("LONG_IMDB_DESCRIPTION", "False"), False)
SPELL_CHECK_REPLY = is_enabled(environ.get("SPELL_CHECK_REPLY", "True"), True)
MAX_LIST_ELM = environ.get("MAX_LIST_ELM", None)
INDEX_REQ_CHANNEL = int(environ.get('INDEX_REQ_CHANNEL', LOG_CHANNEL))
FILE_STORE_CHANNEL = [int(ch) for ch in (environ.get('FILE_STORE_CHANNEL', '')).split()]
MELCOW_NEW_USERS = is_enabled((environ.get('MELCOW_NEW_USERS', "True")), True)
PROTECT_CONTENT = is_enabled((environ.get('PROTECT_CONTENT', "False")), False)
PUBLIC_FILE_STORE = is_enabled((environ.get('PUBLIC_FILE_STORE', "False")), True)
SHORTLINK_URL = environ.get("SHORTLINK_URL", "instantearn.in")
SHORTLINK_API = environ.get("SHORTLINK_API", "85738b1e5dc3dc11333d57b84db5200978d82ec7")
VERIFY_EXPIRE = int(environ.get('VERIFY_EXPIRE', 86400)) # Add time in seconds
IS_VERIFY = is_enabled(environ.get("IS_VERIFY", "False"), False)

LOG_STR = "Current Cusomized Configurations are:-\n"
LOG_STR += ("IMDB Results are enabled, Bot will be showing imdb details for you queries.\n" if IMDB else "IMBD Results are disabled.\n")
LOG_STR += ("P_TTI_SHOW_OFF found , Users will be redirected to send /start to Bot PM instead of sending file file directly\n" if P_TTI_SHOW_OFF else "P_TTI_SHOW_OFF is disabled files will be send in PM, instead of sending start.\n")
LOG_STR += ("SINGLE_BUTTON is Found, filename and files size will be shown in a single button instead of two separate buttons\n" if SINGLE_BUTTON else "SINGLE_BUTTON is disabled , filename and file_sixe will be shown as different buttons\n")
LOG_STR += (f"CUSTOM_FILE_CAPTION enabled with value {CUSTOM_FILE_CAPTION}, your files will be send along with this customized caption.\n" if CUSTOM_FILE_CAPTION else "No CUSTOM_FILE_CAPTION Found, Default captions of file will be used.\n")
LOG_STR += ("Long IMDB storyline enabled." if LONG_IMDB_DESCRIPTION else "LONG_IMDB_DESCRIPTION is disabled , Plot will be shorter.\n")
LOG_STR += ("Spell Check Mode Is Enabled, bot will be suggesting related movies if movie not found\n" if SPELL_CHECK_REPLY else "SPELL_CHECK_REPLY Mode disabled\n")
LOG_STR += (f"MAX_LIST_ELM Found, long list will be shortened to first {MAX_LIST_ELM} elements\n" if MAX_LIST_ELM else "Full List of casts and crew will be shown in imdb template, restrict them by adding a value to MAX_LIST_ELM\n")
LOG_STR += f"Your current IMDB template is {IMDB_TEMPLATE}"
