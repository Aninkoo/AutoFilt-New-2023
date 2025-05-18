import asyncio
import re, time
import ast
import math
import random
import pytz
from datetime import datetime, timedelta, date, time
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from urllib.parse import quote
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, \
    make_inactive
from info import *
from info import ADMINS, AUTH_CHANNEL, BIN_CHANNEL, URL, IS_VERIFY, VERIFY_EXPIRE, SHORTLINK_API, SHORTLINK_URL, AUTH_USERS, DAILY_UPDATE_LINK, IS_STREAM, SUPPORT_CHAT_ID, SUPPORT_CHAT, CUSTOM_FILE_CAPTION, PICS, AUTH_GROUPS, P_TTI_SHOW_OFF, NOR_IMG, LOG_CHANNEL, SPELL_IMG, MAX_B_TN, IMDB, \
    SINGLE_BUTTON, SPELL_CHECK_REPLY, IMDB_TEMPLATE, NO_RESULTS_MSG
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from utils import get_size, is_subscribed, get_poster, get_shortlink, get_verify_status, update_verify_status, get_readable_time, search_gagala, temp, get_settings, save_group_settings, send_all, send_react
from database.users_chats_db import db
from database.ia_filterdb import Media, get_file_details, get_search_results, get_bad_files
from database.filters_mdb import (
    del_all,
    find_filter,
    get_filters,
)
from database.gfilters_mdb import (
    find_gfilter,
    get_gfilters,
    del_allg
)
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

BUTTONS = {}
SPELL_CHECK = {}
CAP = {}

@Client.on_callback_query(filters.regex(r"^stream"))
async def stream_downloader(bot, query):
    if not IS_STREAM:
        await query.answer("Streaming Feature is Temporarily Disabled Due to Budget Problem 😓",show_alert=True)
        return
    file_id = query.data.split('#', 1)[1]
    msg = await bot.send_cached_media(
        chat_id=BIN_CHANNEL,
        file_id=file_id)
    online = f"{URL}watch/{msg.id}"
    download = f"{URL}download/{msg.id}"
    await query.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("ᴡᴀᴛᴄʜ ᴏɴʟɪɴᴇ", url=online),
                InlineKeyboardButton("ꜰᴀsᴛ ᴅᴏᴡɴʟᴏᴀᴅ", url=download)
            ],[
                InlineKeyboardButton('⁉️ ᴄʟᴏsᴇ ⁉️', callback_data='close_data')
            ]
        ]
    ))

@Client.on_message(filters.group & filters.service)
async def left_chat(client, message):
    await message.delete()

@Client.on_message(filters.group & filters.text & filters.incoming)
async def give_filter(client, message):
    
    if message.chat.id == SUPPORT_CHAT_ID:
        search = message.text
        temp_files, temp_offset, total_results = await get_search_results(chat_id=message.chat.id, query=search.lower(), offset=0, filter=True)
        if total_results == 0:
            return
        else:
            buttons = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton('PaxMOVIES Group', url="https://t.me/paxmovies")]
                ]
            )
            await message.reply_text(
                f"👋 𝖧𝖾𝗒 <b>{message.from_user.mention}</b> \n📁 <b>{str(total_results)}</b> 𝖱𝖾𝗌𝗎𝗅𝗍𝗌 𝖺𝗋𝖾 𝖿𝗈𝗎𝗇𝖽 𝖿𝗈𝗋 𝗒𝗈𝗎𝗋 𝗊𝗎𝖾𝗋𝗒: <b>{search}</b>.\n\nBut you can not get it here! \n <b>👇 Search here 👇</b>",
                reply_markup=buttons
            )
        try:
            await message.delete()
        except:
            pass       
    else: #a better logic to avoid repeated lines of code in auto_filter function
        glob = await global_filters(client, message)
        if glob == False:
            manual = await manual_filters(client, message)
            if manual == False:
                settings = await get_settings(message.chat.id)
                try:
                    if settings['auto_ffilter']:
                        await auto_filter(client, message)
                except KeyError:
                    grpid = await active_connection(str(message.from_user.id))
                    await save_group_settings(grpid, 'auto_ffilter', True)
                    settings = await get_settings(message.chat.id)
                    if settings['auto_ffilter']:
                        await auto_filter(client, message)

@Client.on_message(filters.private & filters.text & filters.incoming)
async def pv_filter(client, message):
    if message.text.startswith("/"):
        return
    if message.text.startswith("http"):
        return
    user_id = message.from_user.id
    if user_id in ADMINS:
        glob = await global_filters(client, message)
        if glob == False:
            manual = await manual_filters(client, message)
            if manual == False:
                await auto_filter(client, message)
        return # ignore admins
    stick = await message.reply_sticker(sticker="CAACAgQAAxkBAdumNGfK4Rcgb3VPtirCHpiZTsf8fExbAAKmDwACdo5YU0nvPPPp_97lNgQ")
    search = message.text
    files, n_offset, total = await get_search_results(0, query=search.lower(), offset=0, filter=True)
    if int(total) != 0:
        btn = [[
            InlineKeyboardButton('PaxMOVIES Group', url="https://t.me/paxmovies"),
            #InlineKeyboardButton('📥 Search Now! 📥', url=f"http://t.me/{temp.U_NAME}?start=SEARCH-{search_with_underscore}")
        ]]
        pvt_msg = await message.reply_text(f'👋 𝖧𝖾𝗒 <b>{message.from_user.mention}</b> \n📁 <b>{str(total)}</b> 𝖱𝖾𝗌𝗎𝗅𝗍𝗌 𝖺𝗋𝖾 𝖿𝗈𝗎𝗇𝖽 𝖿𝗈𝗋 𝗒𝗈𝗎𝗋 𝗊𝗎𝖾𝗋𝗒: <b>{search}</b>.\n\nBut you can not get it here! \n <b>👇 Search here 👇</b>"', reply_markup=InlineKeyboardMarkup(btn), quote=True)
        await stick.delete()
        await asyncio.sleep(120)
        await pvt_msg.delete()
        await message.delete()
    else:
        await stick.delete()
        google_search = search.replace(" ", "+")
        button = [[
            InlineKeyboardButton("🔎 Our Group 🔍", url=f"https://t.me/paxmovies")
        ]]
        
        n = await message.reply_photo(
            photo=SPELL_IMG, 
            caption="❌ <b>Sᴏʀʀʏ, I ᴄᴏᴜʟᴅ ɴᴏᴛ ғɪɴᴅ ᴀɴʏᴛʜɪɴɢ ʀᴇʟᴀᴛᴛᴇᴅ ᴛᴏ ᴛʜᴀᴛ!\n\nPʟᴇᴀsᴇ sᴇᴀʀᴄʜ ɪɴ ᴛʜᴇ Gʀᴏᴜᴘ sᴏ ᴛʜᴀᴛ I ᴄᴀɴ ʀᴇᴘᴏʀᴛᴇᴅ ɪᴛ ᴛᴏ ADMIN ᴀɴᴅ ɪᴛ ᴡɪʟʟ ʙᴇ ᴀᴅᴅᴇᴅ ᴛᴏ ᴍʏ Dᴀᴛᴀʙᴀsᴇ sᴏᴏɴ ɪғ ʀᴇʟᴇᴀsᴇᴅ.</b>",
            reply_markup=InlineKeyboardMarkup(button)
        )
        await asyncio.sleep(60)
        await n.delete()
        await message.delete()

@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    try:
        offset = int(offset)
    except:
        offset = 0
    search = BUTTONS.get(key)
    cap = CAP.get(key)
    if not search:
        await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True)
        return

    files, n_offset, total = await get_search_results(query.message.chat.id, search, offset=offset, filter=True)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0

    if not files:
        return
    settings = await get_settings(query.message.chat.id)
    pre = 'filep' if settings['file_secure'] else 'file'
    temp.FILES_IDS[key] = files
    files_link = ''
    end_cap = ''
    if settings['button']:
        btn = [
            [
                InlineKeyboardButton(
                   text=f"📂{get_size(file.file_size)} 🎥{file.file_name}", callback_data=f'{pre}#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = []
        end_cap = f"""© @paxtv"""
        for file in files:
            files_link += f"<b>📁 {get_size(file.file_size)} <a href=https://t.me/{temp.U_NAME}?start={pre}_{file.file_id}> ▷ {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file.file_name.split()))}\n\n</a></b>"
    try:
        if settings['button']:
            btn.insert(0, 
            [
                InlineKeyboardButton(f'📟 𝖥𝗂𝗅𝖾𝗌: {len(files)}', 'dupe'),
                InlineKeyboardButton(f'📮 Info', 'tips'),
                InlineKeyboardButton(f'🎁 𝖳𝗂𝗉𝗌', 'info')
            ]
            )

                
    except KeyError:
        grpid = await active_connection(str(query.message.from_user.id))
        await save_group_settings(grpid, 'auto_delete', True)
        settings = await get_settings(query.message.chat.id)
        if settings['button']:
            btn.insert(0, 
            [
                InlineKeyboardButton(f'📟 𝖥𝗂𝗅𝖾𝗌: {len(files)}', 'dupe'),
                InlineKeyboardButton(f'📮 Info', 'tips'),
                InlineKeyboardButton(f'🎁 𝖳𝗂𝗉𝗌', 'info')
            ]
            )

    try:
        settings = await get_settings(query.message.chat.id)
        if settings['max_btn']:
            if 0 < offset <= 10:
                off_set = 0
            elif offset == 0:
                off_set = None
            else:
                off_set = offset - 10
            if n_offset == 0:
                btn.append(
                    [InlineKeyboardButton("◀️ 𝖡ᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages")]
                )
            elif off_set is None:
                btn.append([InlineKeyboardButton("📃", callback_data="pages"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"), InlineKeyboardButton("𝖭𝖤𝖷𝖳 ▶️", callback_data=f"next_{req}_{key}_{n_offset}")])
            else:
                btn.append(
                    [
                        InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                        InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"),
                        InlineKeyboardButton("𝖭ᴇxᴛ ▶️", callback_data=f"next_{req}_{key}_{n_offset}")
                    ],
                )
        else:
            if 0 < offset <= int(MAX_B_TN):
                off_set = 0
            elif offset == 0:
                off_set = None
            else:
                off_set = offset - int(MAX_B_TN)
            if n_offset == 0:
                btn.append(
                    [InlineKeyboardButton("◀️ 𝖡ᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages")]
                )
            elif off_set is None:
                btn.append([InlineKeyboardButton("📃", callback_data="pages"), InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages"), InlineKeyboardButton("𝖭𝖤𝖷𝖳 ▶️", callback_data=f"next_{req}_{key}_{n_offset}")])
            else:
                btn.append(
                    [
                        InlineKeyboardButton("◀️ 𝖡ᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                        InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages"),
                        InlineKeyboardButton("𝖭ᴇxᴛ ▶️", callback_data=f"next_{req}_{key}_{n_offset}")
                    ],
                )
    except KeyError:
        await save_group_settings(query.message.chat.id, 'max_btn', False)
        settings = await get_settings(query.message.chat.id)
        if settings['max_btn']:
            if 0 < offset <= 10:
                off_set = 0
            elif offset == 0:
                off_set = None
            else:
                off_set = offset - 10
            if n_offset == 0:
                btn.append(
                    [InlineKeyboardButton("◀️ 𝖡ᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages")]
                )
            elif off_set is None:
                btn.append([InlineKeyboardButton("📃", callback_data="pages"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"), InlineKeyboardButton("𝖭𝖤𝖷𝖳 ▶️", callback_data=f"next_{req}_{key}_{n_offset}")])
            else:
                btn.append(
                    [
                        InlineKeyboardButton("◀️ 𝖡ᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                        InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"),
                        InlineKeyboardButton("𝖭ᴇxᴛ ▶️", callback_data=f"next_{req}_{key}_{n_offset}")
                    ],
                )
        else:
            if 0 < offset <= int(MAX_B_TN):
                off_set = 0
            elif offset == 0:
                off_set = None
            else:
                off_set = offset - int(MAX_B_TN)
            if n_offset == 0:
                btn.append(
                    [InlineKeyboardButton("◀️ 𝖡ᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages")]
                )
            elif off_set is None:
                btn.append([InlineKeyboardButton("📃", callback_data="pages"), InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages"), InlineKeyboardButton("𝖭𝖤𝖷𝖳 ▶️", callback_data=f"next_{req}_{key}_{n_offset}")])
            else:
                btn.append(
                    [
                        InlineKeyboardButton("◀️ 𝖡ᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                        InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages"),
                        InlineKeyboardButton("𝖭ᴇxᴛ ▶️", callback_data=f"next_{req}_{key}_{n_offset}")
                    ],
                )

    btn.insert(0,
               [
                   InlineKeyboardButton("Lᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}#{req}#{offset}"),
                   InlineKeyboardButton("Sᴇᴀsᴏɴ", callback_data=f"seasons#{key}#{req}#{offset}"),
                   InlineKeyboardButton("Qᴜᴀʟɪᴛʏ", callback_data=f"qualities#{key}#{req}#{offset}")
               ]
              )
    btn.insert(0, [
        InlineKeyboardButton(f'🎬 {search} 🎬', 'rkbtn')
    ])
    try:
        await query.message.edit_text(cap + files_link + end_cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)
    except MessageNotModified:
        pass
    await query.answer()

@Client.on_callback_query(filters.regex(r"^languages"))
async def languages_cb_handler(client: Client, query: CallbackQuery):
    _, key, req, offset = query.data.split("#")
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    langs = ['english', 'tamil', 'hindi', 'malayalam', 'telugu', 'kannada']
    
    btn = [
        [
            InlineKeyboardButton(
                text=lang.title(),
                callback_data=f"lang_search#{lang}#{key}#{offset}#{req}"
            ) for lang in langs[i:i+2]  # Taking 2 items per row
        ]
        for i in range(0, len(langs), 2)
    ]

    btn.append([InlineKeyboardButton(text="⪻ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ", callback_data=f"next_{req}_{key}_{offset}")])
    await query.message.edit_text("<b>ɪɴ ᴡʜɪᴄʜ ʟᴀɴɢᴜᴀɢᴇ ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ, sᴇʟᴇᴄᴛ ʜᴇʀᴇ</b>", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(btn))

@Client.on_callback_query(filters.regex(r"^lang_search"))
async def filter_languages_cb_handler(client: Client, query: CallbackQuery):
    _, lang, key, offset, req = query.data.split("#")
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        
    search = BUTTONS.get(key)
    cap = CAP.get(key)
    if not search:
        await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True)
        return 

    files, l_offset, total_results = await get_search_results(query.message.chat.id, search, filter=True, lang=lang)
    if not files:
        await query.answer(f"😢 Sᴏʀʀʏ, '{lang.title()}' Lᴀɴɢᴜᴀɢᴇ ғɪʟᴇs ɴᴏᴛ ғᴏᴜɴᴅ \n\n ✅ Cʜᴇᴄᴋ ᴡʜᴇᴛʜᴇʀ Mᴏᴠɪᴇ ɪs ʀᴇᴀʟᴇsᴇᴅ ɪɴ '{lang.title()}' ʟᴀɴɢᴜᴀɢᴇ ɪɴ #Google \n\n", show_alert=1)
        return
    settings = await get_settings(query.message.chat.id)
    pre = 'filep' if settings['file_secure'] else 'file'
    files_link = ''
    end_cap = ""
    temp.FILES[key] = files
    if settings['button']:
        btn = [
            [
                InlineKeyboardButton(
                   text=f"📂{get_size(file.file_size)} 🎥{file.file_name}", callback_data=f'{pre}#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = []
        end_cap = f"""© @paxtv"""
        for file in files:
            files_link += f"<b>📁 {get_size(file.file_size)} <a href=https://t.me/{temp.U_NAME}?start={pre}_{file.file_id}> ▷ {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file.file_name.split()))}\n\n</a></b>"
    try:
        if settings['button']:
            btn.insert(0, 
            [
                InlineKeyboardButton(f'📟 𝖥𝗂𝗅𝖾𝗌: {len(files)}', 'dupe'),
                InlineKeyboardButton(f'📮 Info', 'tips'),
                InlineKeyboardButton(f'🎁 𝖳𝗂𝗉𝗌', 'info')
            ]
            )

                
    except KeyError:
        grpid = await active_connection(str(query.message.from_user.id))
        await save_group_settings(grpid, 'auto_delete', True)
        settings = await get_settings(query.message.chat.id)
        if settings['button']:
            btn.insert(0, 
            [
                InlineKeyboardButton(f'📟 𝖥𝗂𝗅𝖾𝗌: {len(files)}', 'dupe'),
                InlineKeyboardButton(f'📮 Info', 'tips'),
                InlineKeyboardButton(f'🎁 𝖳𝗂𝗉𝗌', 'info')
            ]
            )

    if l_offset != "":
        btn.append(
            [InlineKeyboardButton(text=f"Pᴀɢᴇs 1 / {math.ceil(int(total_results) / 10)}", callback_data="pages"),
             InlineKeyboardButton(text="𝖭ᴇxᴛ ▶️", callback_data=f"lang_next#{req}#{key}#{lang}#{l_offset}#{offset}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton(text="🚸 ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇs 🚸", callback_data="pages")]
        )
    btn.append([InlineKeyboardButton(text="⪻ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ", callback_data=f"next_{req}_{key}_{offset}")])
    await query.message.edit_text(cap + files_link + end_cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)


@Client.on_callback_query(filters.regex(r"^lang_next"))
async def lang_next_page(bot, query):
    ident, req, key, lang, l_offset, offset = query.data.split("#")
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    try:
        l_offset = int(l_offset)
    except:
        l_offset = 0

    settings = await get_settings(query.message.chat.id)
    search = BUTTONS.get(key)
    cap = CAP.get(key)
    pre = 'filep' if settings['file_secure'] else 'file'
    files_link = ''
    end_cap = ""
    if not search:
        await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True)
        return 

    files, n_offset, total = await get_search_results(query.message.chat.id, search, filter=True, offset=l_offset, lang=lang)
    if not files:
        return
    temp.FILES[key] = files
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0
    if settings['button']:
        btn = [
            [
                InlineKeyboardButton(
                   text=f"📂{get_size(file.file_size)} 🎥{file.file_name}", callback_data=f'{pre}#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = []
        end_cap = f"""© @paxtv"""
        for file in files:
            files_link += f"<b>📁 {get_size(file.file_size)} <a href=https://t.me/{temp.U_NAME}?start={pre}_{file.file_id}> ▷ {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file.file_name.split()))}\n\n</a></b>"
            
    try:
        if settings['button']:
            btn.insert(0, 
            [
                InlineKeyboardButton(f'📟 𝖥𝗂𝗅𝖾𝗌: {len(files)}', 'dupe'),
                InlineKeyboardButton(f'📮 Info', 'tips'),
                InlineKeyboardButton(f'🎁 𝖳𝗂𝗉𝗌', 'info')
            ]
            )

                
    except KeyError:
        grpid = await active_connection(str(query.message.from_user.id))
        await save_group_settings(grpid, 'auto_delete', True)
        settings = await get_settings(query.message.chat.id)
        if settings['button']:
            btn.insert(0, 
            [
                InlineKeyboardButton(f'📟 𝖥𝗂𝗅𝖾𝗌: {len(files)}', 'dupe'),
                InlineKeyboardButton(f'📮 Info', 'tips'),
                InlineKeyboardButton(f'🎁 𝖳𝗂𝗉𝗌', 'info')
            ]
            )

    if 0 < l_offset <= 10:
        b_offset = 0
    elif l_offset == 0:
        b_offset = None
    else:
        b_offset = l_offset - 10

    if n_offset == 0:
        btn.append(
            [InlineKeyboardButton("◀️ 𝖡ᴀᴄᴋ", callback_data=f"lang_next#{req}#{key}#{lang}#{b_offset}#{offset}"),
             InlineKeyboardButton(f"Pᴀɢᴇs {math.ceil(int(l_offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages")]
        )
    elif b_offset is None:
        btn.append(
            [InlineKeyboardButton(f"Pᴀɢᴇs {math.ceil(int(l_offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
             InlineKeyboardButton("𝖭ᴇxᴛ ▶️", callback_data=f"lang_next#{req}#{key}#{lang}#{n_offset}#{offset}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton("◀️ 𝖡ᴀᴄᴋ", callback_data=f"lang_next#{req}#{key}#{lang}#{b_offset}#{offset}"),
             InlineKeyboardButton(f"{math.ceil(int(l_offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
             InlineKeyboardButton("𝖭ᴇxᴛ ▶️", callback_data=f"lang_next#{req}#{key}#{lang}#{n_offset}#{offset}")]
        )
    btn.append([InlineKeyboardButton(text="⪻ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ", callback_data=f"next_{req}_{key}_{offset}")])
    await query.message.edit_text(cap + files_link + end_cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex(r"^qualities"))
async def qualities_cb_handler(client: Client, query: CallbackQuery):
    _, key, req, offset = query.data.split("#")
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    qualis = ['360p', '480p', '540p', '720p', '1080p', '2400p']
    
    btn = [
        [
            InlineKeyboardButton(
                text=quali.title(),
                callback_data=f"quali_search#{quali}#{key}#{offset}#{req}"
            ) for quali in qualis[i:i+3]  # Taking 3 items per row
        ]
        for i in range(0, len(qualis), 3)
    ]

    btn.append([InlineKeyboardButton(text="⪻ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ", callback_data=f"next_{req}_{key}_{offset}")])
    await query.message.edit_text("<b>ɪɴ ᴡʜɪᴄʜ Qᴜᴀʟɪᴛʏ ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ? \nsᴇʟᴇᴄᴛ ʜᴇʀᴇ</b>👇", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(btn))
    

@Client.on_callback_query(filters.regex(r"^quali_search"))
async def filter_qualities_cb_handler(client: Client, query: CallbackQuery):
    _, quali, key, offset, req = query.data.split("#")
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        
    search = BUTTONS.get(key)
    cap = CAP.get(key)
    if not search:
        await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True)
        return 

    files, q_offset, total_results = await get_search_results(query.message.chat.id, search, filter=True, lang=quali)
    if not files:
        await query.answer(f"😢 Sᴏʀʀʏ, '{quali.title()}' Qᴜᴀʟɪᴛʏ ɪs ɴᴏᴛ ғᴏᴜɴᴅ \n\n ✅ Cʜᴇᴄᴋ ᴏᴛʜᴇʀ Qᴜᴀʟɪᴛɪᴇs", show_alert=1)
        return
    settings = await get_settings(query.message.chat.id)
    pre = 'filep' if settings['file_secure'] else 'file'
    files_link = ''
    end_cap = ""
    temp.FILES[key] = files
    if settings['button']:
        btn = [
            [
                InlineKeyboardButton(
                   text=f"📂{get_size(file.file_size)} 🎥{file.file_name}", callback_data=f'{pre}#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = []
        end_cap = f"""© @paxtv"""
        for file in files:
            files_link += f"<b>📁 {get_size(file.file_size)} <a href=https://t.me/{temp.U_NAME}?start={pre}_{file.file_id}> ▷ {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file.file_name.split()))}\n\n</a></b>"
    try:
        if settings['button']:
            btn.insert(0, 
            [
                InlineKeyboardButton(f'📟 𝖥𝗂𝗅𝖾𝗌: {len(files)}', 'dupe'),
                InlineKeyboardButton(f'📮 Info', 'tips'),
                InlineKeyboardButton(f'🎁 𝖳𝗂𝗉𝗌', 'info')
            ]
            )

                
    except KeyError:
        grpid = await active_connection(str(query.message.from_user.id))
        await save_group_settings(grpid, 'auto_delete', True)
        settings = await get_settings(query.message.chat.id)
        if settings['button']:
            btn.insert(0, 
            [
                InlineKeyboardButton(f'📟 𝖥𝗂𝗅𝖾𝗌: {len(files)}', 'dupe'),
                InlineKeyboardButton(f'📮 Info', 'tips'),
                InlineKeyboardButton(f'🎁 𝖳𝗂𝗉𝗌', 'info')
            ]
            )

    if q_offset != "":
        btn.append(
            [InlineKeyboardButton(text=f"Pᴀɢᴇs 1 / {math.ceil(int(total_results) / 10)}", callback_data="pages"),
             InlineKeyboardButton(text="𝖭ᴇxᴛ ▶️", callback_data=f"quali_next#{req}#{key}#{quali}#{q_offset}#{offset}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton(text="🚸 ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇs 🚸", callback_data="pages")]
        )
    btn.append([InlineKeyboardButton(text="⪻ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ", callback_data=f"next_{req}_{key}_{offset}")])
    await query.message.edit_text(cap + files_link + end_cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)
                

@Client.on_callback_query(filters.regex(r"^quali_next"))
async def quali_next_page(bot, query):
    ident, req, key, quali, q_offset, offset = query.data.split("#")
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    try:
        q_offset = int(q_offset)
    except:
        q_offset = 0

    settings = await get_settings(query.message.chat.id)
    search = BUTTONS.get(key)
    cap = CAP.get(key)
    pre = 'filep' if settings['file_secure'] else 'file'
    files_link = ''
    end_cap = ""
    if not search:
        await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True)
        return 

    files, n_offset, total = await get_search_results(query.message.chat.id, search, filter=True, offset=q_offset, lang=quali)
    if not files:
        return
    temp.FILES[key] = files
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0
    if settings['button']:
        btn = [
            [
                InlineKeyboardButton(
                   text=f"📂{get_size(file.file_size)} 🎥{file.file_name}", callback_data=f'{pre}#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = []
        end_cap = f"""© @paxtv"""
        for file in files:
            files_link += f"<b>📁 {get_size(file.file_size)} <a href=https://t.me/{temp.U_NAME}?start={pre}_{file.file_id}> ▷ {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file.file_name.split()))}\n\n</a></b>"
            
    try:
        if settings['button']:
            btn.insert(0, 
            [
                InlineKeyboardButton(f'📟 𝖥𝗂𝗅𝖾𝗌: {len(files)}', 'dupe'),
                InlineKeyboardButton(f'📮 Info', 'tips'),
                InlineKeyboardButton(f'🎁 𝖳𝗂𝗉𝗌', 'info')
            ]
            )

                
    except KeyError:
        grpid = await active_connection(str(query.message.from_user.id))
        await save_group_settings(grpid, 'auto_delete', True)
        settings = await get_settings(query.message.chat.id)
        if settings['button']:
            btn.insert(0, 
            [
                InlineKeyboardButton(f'📟 𝖥𝗂𝗅𝖾𝗌: {len(files)}', 'dupe'),
                InlineKeyboardButton(f'📮 Info', 'tips'),
                InlineKeyboardButton(f'🎁 𝖳𝗂𝗉𝗌', 'info')
            ]
            )

    if 0 < q_offset <= 10:
        b_offset = 0
    elif q_offset == 0:
        b_offset = None
    else:
        b_offset = q_offset - 10

    if n_offset == 0:
        btn.append(
            [InlineKeyboardButton("◀️ 𝖡ᴀᴄᴋ", callback_data=f"quali_next#{req}#{key}#{quali}#{b_offset}#{offset}"),
             InlineKeyboardButton(f"Pᴀɢᴇs {math.ceil(int(q_offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages")]
        )
    elif b_offset is None:
        btn.append(
            [InlineKeyboardButton(f"Pᴀɢᴇs {math.ceil(int(q_offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
             InlineKeyboardButton("𝖭ᴇxᴛ ▶️", callback_data=f"quali_next#{req}#{key}#{quali}#{n_offset}#{offset}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton("◀️ 𝖡ᴀᴄᴋ", callback_data=f"quali_next#{req}#{key}#{quali}#{b_offset}#{offset}"),
             InlineKeyboardButton(f"{math.ceil(int(q_offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
             InlineKeyboardButton("𝖭ᴇxᴛ ▶️", callback_data=f"quali_next#{req}#{key}#{quali}#{n_offset}#{offset}")]
        )
    btn.append([InlineKeyboardButton(text="⪻ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ", callback_data=f"next_{req}_{key}_{offset}")])
    await query.message.edit_text(cap + files_link + end_cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex(r"^seasons"))
async def seasons_cb_handler(client: Client, query: CallbackQuery):
    _, key, req, offset = query.data.split("#")
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    seas = ['s01', 's02', 's03', 's04', 's05', 's06', 's07', 's08', 's09', 's10', 's11', 's12']
    
    btn = [
        [
            InlineKeyboardButton(
                text=sea.title(),
                callback_data=f"sea_search#{sea}#{key}#{offset}#{req}"
            ) for sea in seas[i:i+4]  # Taking 4 items per row
        ]
        for i in range(0, len(seas), 4)
    ]

    btn.append([InlineKeyboardButton(text="⪻ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ", callback_data=f"next_{req}_{key}_{offset}")])
    await query.message.edit_text("<b>ɪɴ ᴡʜɪᴄʜ Season ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ? \nsᴇʟᴇᴄᴛ ʜᴇʀᴇ</b>👇", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(btn))
    

@Client.on_callback_query(filters.regex(r"^sea_search"))
async def filter_seasons_cb_handler(client: Client, query: CallbackQuery):
    _, sea, key, offset, req = query.data.split("#")
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        
    search = BUTTONS.get(key)
    cap = CAP.get(key)
    if not search:
        await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True)
        return 

    film = f"{search} {sea}"
    files, s_offset, total_results = await get_search_results(query.message.chat.id, film, filter=True, lang=None)
    if not files:
        await query.answer(f"😢 Sᴏʀʀʏ, '{sea.title()}' Sᴇᴀsᴏɴ ɪs ɴᴏᴛ ғᴏᴜɴᴅ \n\n Yᴏᴜ ᴄᴀɴ Cʜᴇᴄᴋ ᴇᴀʟɪᴇʀ sᴇᴀsᴏɴs", show_alert=1)
        return
    settings = await get_settings(query.message.chat.id)
    pre = 'filep' if settings['file_secure'] else 'file'
    files_link = ''
    end_cap = ""
    temp.FILES[key] = files
    if settings['button']:
        btn = [
            [
                InlineKeyboardButton(
                   text=f"📂{get_size(file.file_size)} 🎥{file.file_name}", callback_data=f'{pre}#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = []
        end_cap = f"""© @paxtv"""
        for file in files:
            files_link += f"<b>📁 {get_size(file.file_size)} <a href=https://t.me/{temp.U_NAME}?start={pre}_{file.file_id}> ▷ {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file.file_name.split()))}\n\n</a></b>"
    try:
        if settings['button']:
            btn.insert(0, 
            [
                InlineKeyboardButton(f'📟 𝖥𝗂𝗅𝖾𝗌: {len(files)}', 'dupe'),
                InlineKeyboardButton(f'📮 Info', 'tips'),
                InlineKeyboardButton(f'🎁 𝖳𝗂𝗉𝗌', 'info')
            ]
            )

                
    except KeyError:
        grpid = await active_connection(str(query.message.from_user.id))
        await save_group_settings(grpid, 'auto_delete', True)
        settings = await get_settings(query.message.chat.id)
        if settings['button']:
            btn.insert(0, 
            [
                InlineKeyboardButton(f'📟 𝖥𝗂𝗅𝖾𝗌: {len(files)}', 'dupe'),
                InlineKeyboardButton(f'📮 Info', 'tips'),
                InlineKeyboardButton(f'🎁 𝖳𝗂𝗉𝗌', 'info')
            ]
            )

    if s_offset != "":
        btn.append(
            [InlineKeyboardButton(text=f"Pᴀɢᴇs 1 / {math.ceil(int(total_results) / 10)}", callback_data="pages"),
             InlineKeyboardButton(text="𝖭ᴇxᴛ ▶️", callback_data=f"sea_next#{req}#{key}#{sea}#{s_offset}#{offset}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton(text="🚸 ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇs 🚸", callback_data="pages")]
        )
    btn.append([InlineKeyboardButton(text="⪻ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ", callback_data=f"next_{req}_{key}_{offset}")])
    await query.message.edit_text(cap + files_link + end_cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex(r"^sea_next"))
async def sea_next_page(bot, query):
    ident, req, key, sea, s_offset, offset = query.data.split("#")
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    try:
        s_offset = int(s_offset)
    except:
        s_offset = 0

    settings = await get_settings(query.message.chat.id)
    search = BUTTONS.get(key)
    cap = CAP.get(key)
    pre = 'filep' if settings['file_secure'] else 'file'
    files_link = ''
    end_cap = ""
    if not search:
        await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True)
        return 

    film = f"{search} {sea}"
    files, n_offset, total = await get_search_results(query.message.chat.id, film, filter=True, offset=s_offset, lang=None)
    if not files:
        return
    temp.FILES[key] = files
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0
    if settings['button']:
        btn = [
            [
                InlineKeyboardButton(
                   text=f"📂{get_size(file.file_size)} 🎥{file.file_name}", callback_data=f'{pre}#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = []
        end_cap = f"""© @paxtv"""
        for file in files:
            files_link += f"<b>📁 {get_size(file.file_size)} <a href=https://t.me/{temp.U_NAME}?start={pre}_{file.file_id}> ▷ {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file.file_name.split()))}\n\n</a></b>"
            
    try:
        if settings['button']:
            btn.insert(0, 
            [
                InlineKeyboardButton(f'📟 𝖥𝗂𝗅𝖾𝗌: {len(files)}', 'dupe'),
                InlineKeyboardButton(f'📮 Info', 'tips'),
                InlineKeyboardButton(f'🎁 𝖳𝗂𝗉𝗌', 'info')
            ]
            )

                
    except KeyError:
        grpid = await active_connection(str(query.message.from_user.id))
        await save_group_settings(grpid, 'auto_delete', True)
        settings = await get_settings(query.message.chat.id)
        if settings['button']:
            btn.insert(0, 
            [
                InlineKeyboardButton(f'📟 𝖥𝗂𝗅𝖾𝗌: {len(files)}', 'dupe'),
                InlineKeyboardButton(f'📮 Info', 'tips'),
                InlineKeyboardButton(f'🎁 𝖳𝗂𝗉𝗌', 'info')
            ]
            )

    if 0 < s_offset <= 10:
        b_offset = 0
    elif s_offset == 0:
        b_offset = None
    else:
        b_offset = s_offset - 10

    if n_offset == 0:
        btn.append(
            [InlineKeyboardButton("◀️ 𝖡ᴀᴄᴋ", callback_data=f"sea_next#{req}#{key}#{sea}#{b_offset}#{offset}"),
             InlineKeyboardButton(f"Pᴀɢᴇs {math.ceil(int(s_offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages")]
        )
    elif b_offset is None:
        btn.append(
            [InlineKeyboardButton(f"Pᴀɢᴇs {math.ceil(int(s_offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
             InlineKeyboardButton("𝖭ᴇxᴛ ▶️", callback_data=f"sea_next#{req}#{key}#{sea}#{n_offset}#{offset}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton("◀️ 𝖡ᴀᴄᴋ", callback_data=f"sea_next#{req}#{key}#{sea}#{b_offset}#{offset}"),
             InlineKeyboardButton(f"{math.ceil(int(s_offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
             InlineKeyboardButton("𝖭ᴇxᴛ ▶️", callback_data=f"sea_next#{req}#{key}#{sea}#{n_offset}#{offset}")]
        )
    btn.append([InlineKeyboardButton(text="⪻ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ", callback_data=f"next_{req}_{key}_{offset}")])
    await query.message.edit_text(cap + files_link + end_cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)


@Client.on_callback_query(filters.regex(r"^spolling"))
async def advantage_spoll_choker(bot, query):
    _, user, movie_ = query.data.split('#')
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    if movie_ == "close_spellcheck":
        return await query.message.delete()
    await query.answer(script.TOP_ALRT_MSG)
    movie_ = movie_.strip()
    gl = await global_filters(bot, query.message, text=movie_)
    if gl == False:
        k = await manual_filters(bot, query.message, text=movie_)
        if k == False:
            files, offset, total_results = await get_search_results(query.message.chat.id, movie_, offset=0, filter=True)
            if files:
                k = (movie_, files, offset, total_results)
                await auto_filter(bot, query, k)
            else:
                reqstr1 = query.from_user.id if query.from_user else 0
                reqstr = await bot.get_users(reqstr1)
                google_search = movie_.replace(" ", "+")
                encoded_search = quote(movie_)
                button = [[
                    InlineKeyboardButton(f'🔎 Tɪᴘs', 'tips'),
                    InlineKeyboardButton(f'📩 Rᴇᴘᴏʀᴛ', 'info')
                ]]
                k = await query.message.edit(script.I_CUDNT, reply_markup=InlineKeyboardMarkup(button))
                await asyncio.sleep(60)
                await k.delete()

 
@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
    elif query.data == "gfiltersdeleteallconfirm":
        await del_allg(query.message, 'gfilters')
        await query.answer("Done !")
        return
    elif query.data == "gfiltersdeleteallcancel": 
        await query.message.reply_to_message.delete()
        await query.message.delete()
        await query.answer("Process Cancelled !")
        return
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            grpid = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    await query.message.edit_text("Make sure I'm present in your group!!", quote=True)
                    return await query.answer('♻️ Please Share and Support ♻️')
            else:
                await query.message.edit_text(
                    "I'm not connected to any groups!\nCheck /connections or connect to any groups",
                    quote=True
                )
                return await query.answer('♻️ Please Share and Support ♻️')

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            return await query.answer('🔁 Processing.... 🔁')

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
            await del_all(query.message, grp_id, title)
        else:
            await query.answer("You need to be Group Owner or an Auth User to do that!", show_alert=True)
    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer("That's not for you!!", show_alert=True)
    elif "groupcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        if act == "":
            stat = "CONNECT"
            cb = "connectcb"
        else:
            stat = "DISCONNECT"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
             InlineKeyboardButton("DELETE", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("BACK", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"Group Name : **{title}**\nGroup ID : `{group_id}`",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return await query.answer('𝖯𝗂𝗋𝖺𝖼𝗒 𝗂𝗌 𝖢𝗋𝗂𝗆𝖾 !')
    elif "connectcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title

        user_id = query.from_user.id

        mkact = await make_active(str(user_id), str(group_id))

        if mkact:
            await query.message.edit_text(
                f"Connected to **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text('Disconnected from', parse_mode=enums.ParseMode.MARKDOWN)
        return await query.answer('𝖯𝗂𝗋𝖺𝖼𝗒 𝗂𝗌 𝖢𝗋𝗂𝗆𝖾 !')
    elif "disconnect" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title
        user_id = query.from_user.id

        mkinact = await make_inactive(str(user_id))

        if mkinact:
            await query.message.edit_text(
                f"Disconnected from **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer('𝖯𝗂𝗋𝖺𝖼𝗒 𝗂𝗌 𝖢𝗋𝗂𝗆𝖾 !')
    elif "deletecb" in query.data:
        await query.answer()

        user_id = query.from_user.id
        group_id = query.data.split(":")[1]

        delcon = await delete_connection(str(user_id), str(group_id))

        if delcon:
            await query.message.edit_text(
                "Successfully deleted connection"
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer('♻️ Please Share and Support ♻️')
    elif query.data == "backcb":
        await query.answer()

        userid = query.from_user.id

        groupids = await all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text(
                "There are no active connections!! Connect to some groups first.",
            )
            return await query.answer('♻️ Please Share and Support ♻️')
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                        )
                    ]
                )
            except:
                pass
        if buttons:
            await query.message.edit_text(
                "Your connected group details ;\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    elif "gfilteralert" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_gfilter('gfilters', keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
    if query.data.startswith("file"):
        clicked = query.from_user.id
        try:
            typed = query.message.reply_to_message.from_user.id
        except:
            typed = query.from_user.id
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = script.CAPTION
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = sript.CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"

        try:
            if AUTH_CHANNEL and not await is_subscribed(client, query):
                if clicked == typed:
                    await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                    return
                else:
                    await query.answer(f"𝖧𝖾𝗒 {query.from_user.first_name}, Don't Touch other's Request !", show_alert=True)
            elif settings['botpm']:
                if clicked == typed:
                    await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                    return
                else:
                    await query.answer(f"𝖧𝖾𝗒 {query.from_user.first_name}, Don't Touch other's Request !", show_alert=True)
            else:
                if clicked == typed:
                    await client.send_cached_media(
                        chat_id=query.from_user.id,
                        file_id=file_id,
                        caption=f_caption,
                        protect_content=False if ident == "filep" else False,
                        reply_markup=InlineKeyboardMarkup( [ [ InlineKeyboardButton('⭕ 𝗝𝗼𝗶𝗻 𝗠𝗮𝗶𝗻 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 ⭕', url='https://t.me/isaimini_updates') ],[InlineKeyboardButton("✛ ᴡᴀᴛᴄʜ & ᴅᴏᴡɴʟᴏᴀᴅ ✛", callback_data=f"stream#{file.file_id}")]] ))
                else:
                    await query.answer(f"𝖧𝖾𝗒 {query.from_user.first_name}, Don't Touch other's Request !", show_alert=True)
                await query.answer('𝖢𝗁𝖾𝖼𝗄 𝖯𝖬, 𝖨 𝗁𝖺𝗏𝖾 𝗌𝖾𝗇𝗍 𝖿𝗂𝗅𝖾𝗌 𝗂𝗇 𝖯𝖬', show_alert=True)
        except UserIsBlocked:
            await query.answer('𝖴𝗇𝖻𝗅𝗈𝖼𝗄 𝗍𝗁𝖾 𝖻𝗈𝗍 𝗆𝖺𝗇𝗁 !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
        except Exception as e:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
    elif query.data.startswith("checksub"):
        if AUTH_CHANNEL and not await is_subscribed(client, query):
            await query.answer("𝖨 𝖫𝗂𝗄𝖾 𝖸𝗈𝗎𝗋 𝖲𝗆𝖺𝗋𝗍𝗇𝖾𝗌𝗌, 𝖡𝗎𝗍 𝖣𝗈𝗇'𝗍 𝖡𝖾 𝖮𝗏𝖾𝗋𝗌𝗆𝖺𝗋𝗍 😉 \n𝖩𝗈𝗂𝗇 𝖴𝗉𝖽𝖺𝗍𝖾 𝖢𝗁𝖺𝗇𝗇𝖾𝗅 𝖿𝗂𝗋𝗌𝗍 ;)", show_alert=True)
            return
        ident, file_id = query.data.split("#")
        pre='filep' if ident == "checksubp" else 'file'
        await query.answer(url=f"https://t.me/{temp.U_NAME}?start={pre}_{file_id}")
    elif query.data == "pages":
        await query.answer()

    elif query.data.startswith("send_all"):
        _, req, key, pre = query.data.split("#")
        if int(req) not in [query.from_user.id, 0]:
            return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        
        await query.answer(url=f"https://t.me/{temp.U_NAME}?start=all_{key}_{pre}")
        

    elif query.data.startswith("killfilesdq"):
        ident, keyword = query.data.split("#")
        await query.message.edit_text(f"<b>Fetching Files for your query {keyword} on DB... Please wait...</b>")
        files, total = await get_bad_files(keyword)
        await query.message.edit_text(f"<b>Found {total} files for your query {keyword} !\n\nFile deletion process will start in 5 seconds !</b>")
        await asyncio.sleep(5)
        deleted = 0
        async with lock:
            try:
                for file in files:
                    file_ids = file.file_id
                    file_name = file.file_name
                    result = await Media.collection.delete_one({
                        '_id': file_ids,
                    })
                    if result.deleted_count:
                        logger.info(f'File Found for your query {keyword}! Successfully deleted {file_name} from database.')
                    deleted += 1
                    if deleted % 20 == 0:
                        await query.message.edit_text(f"<b>Process started for deleting files from DB. Successfully deleted {str(deleted)} files from DB for your query {keyword} !\n\nPlease wait...</b>")
            except Exception as e:
                logger.exception(e)
                await query.message.edit_text(f'Error: {e}')
            else:
                await query.message.edit_text(f"<b>Process Completed for file deletion !\n\nSuccessfully deleted {str(deleted)} files from database for your query {keyword}.</b>")

    elif query.data.startswith("opnsetgrp"):
        ident, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        st = await client.get_chat_member(grp_id, userid)
        if (
                st.status != enums.ChatMemberStatus.ADMINISTRATOR
                and st.status != enums.ChatMemberStatus.OWNER
                and str(userid) not in ADMINS
        ):
            await query.answer("𝖸𝗈𝗎 𝖽𝗈𝗇'𝗍 𝗁𝖺𝗏𝖾 𝗋𝗂𝗀𝗁𝗍𝗌 𝗍𝗈 𝖽𝗈 𝗍𝗁𝗂𝗌 !", show_alert=True)
            return
        title = query.message.chat.title
        settings = await get_settings(grp_id)
        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('𝖥𝗂𝗅𝗍𝖾𝗋 𝖡𝗎𝗍𝗍𝗈𝗇',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}'),
                    InlineKeyboardButton('𝖲𝗂𝗇𝗀𝗅𝖾 𝖡𝗎𝗍𝗍𝗈𝗇' if settings["button"] else '𝖣𝗈𝗎𝖻𝗅𝖾',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝖥𝗂𝗅𝖾 𝖲𝖾𝗇𝖽 𝖬𝗈𝖽𝖾', callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}'),
                    InlineKeyboardButton('𝖬𝖺𝗇𝗎𝖺𝗅 𝖲𝗍𝖺𝗋𝗍' if settings["botpm"] else '𝖠𝗎𝗍𝗈 𝖲𝖾𝗇𝖽',
                                         callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝖯𝗋𝗈𝗍𝖾𝖼𝗍 𝖢𝗈𝗇𝗍𝖾𝗇𝗍',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝖮𝗇' if settings["file_secure"] else '❌ 𝖮𝖿𝖿',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝖨𝖬𝖣𝖻', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝖮𝗇' if settings["imdb"] else '❌ 𝖮𝖿𝖿',
                                         callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝖲𝗉𝖾𝗅𝗅 𝖢𝗁𝖾𝖼𝗄',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝖮𝗇' if settings["spell_check"] else '❌ 𝖮𝖿𝖿',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝖶𝖾𝗅𝖼𝗈𝗆𝖾 𝖬𝖾𝗌𝗌𝖺𝗀𝖾', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝖮𝗇' if settings["welcome"] else '❌ 𝖮𝖿𝖿',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝖠𝗎𝗍𝗈 𝖣𝖾𝗅𝖾𝗍𝖾',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}'),
                    InlineKeyboardButton('5 𝖬𝗂𝗇' if settings["auto_delete"] else '❌ 𝖮𝖿𝖿',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝖠𝗎𝗍𝗈-𝖥𝗂𝗅𝗍𝖾𝗋',
                                         callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝖮𝗇' if settings["auto_ffilter"] else '❌ 𝖮𝖿𝖿',
                                         callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝖬𝖺𝗑 𝖡𝗎𝗍𝗍𝗈𝗇𝗌',
                                         callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(grp_id)}'),
                    InlineKeyboardButton('10' if settings["max_btn"] else f'{MAX_B_TN}',
                                         callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(grp_id)}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_text(
                text=f"<b>𝖢𝗁𝖺𝗇𝗀𝖾 𝖸𝗈𝗎𝗋 𝖲𝖾𝗍𝗍𝗂𝗇𝗀𝗌 𝖥𝗈𝗋 {title} 𝖠𝗌 𝖸𝗈𝗎𝗋 𝖶𝗂𝗌𝗁</b>",
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML
            )
            await query.message.edit_reply_markup(reply_markup)
        
    elif query.data.startswith("opnsetpm"):
        ident, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        st = await client.get_chat_member(grp_id, userid)
        if (
                st.status != enums.ChatMemberStatus.ADMINISTRATOR
                and st.status != enums.ChatMemberStatus.OWNER
                and str(userid) not in ADMINS
        ):
            await query.answer("𝖸𝗈𝗎 𝖽𝗈𝗇'𝗍 𝗁𝖺𝗏𝖾 𝗋𝗂𝗀𝗁𝗍𝗌 𝗍𝗈 𝖽𝗈 𝗍𝗁𝗂𝗌 !", show_alert=True)
            return
        title = query.message.chat.title
        settings = await get_settings(grp_id)
        btn2 = [[
                 InlineKeyboardButton("➡ 𝖮𝗉𝖾𝗇 𝗂𝗇 𝖯𝖬 ➡", url=f"t.me/{temp.U_NAME}")
               ]]
        reply_markup = InlineKeyboardMarkup(btn2)
        await query.message.edit_text(f"<b>𝖸𝗈𝗎𝗋 𝗌𝖾𝗍𝗍𝗂𝗇𝗀𝗌 𝗆𝖾𝗇𝗎 𝖿𝗈𝗋 {title} 𝗁𝖺𝗌 𝖻𝖾𝖾𝗇 𝗌𝖾𝗇𝗍 𝗍𝗈 𝗒𝗈𝗎𝗋 𝖯𝖬</b>")
        await query.message.edit_reply_markup(reply_markup)
        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('𝖥𝗂𝗅𝗍𝖾𝗋 𝖡𝗎𝗍𝗍𝗈𝗇',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}'),
                    InlineKeyboardButton('𝖲𝗂𝗇𝗀𝗅𝖾 𝖡𝗎𝗍𝗍𝗈𝗇' if settings["button"] else '𝖣𝗈𝗎𝖻𝗅𝖾',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝖥𝗂𝗅𝖾 𝖲𝖾𝗇𝖽 𝖬𝗈𝖽𝖾', callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}'),
                    InlineKeyboardButton('𝖬𝖺𝗇𝗎𝖺𝗅 𝖲𝗍𝖺𝗋𝗍' if settings["botpm"] else '𝖠𝗎𝗍𝗈 𝖲𝖾𝗇𝖽',
                                         callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝖯𝗋𝗈𝗍𝖾𝖼𝗍 𝖢𝗈𝗇𝗍𝖾𝗇𝗍',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝖮𝗇' if settings["file_secure"] else '❌ 𝖮𝖿𝖿',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝖨𝖬𝖣𝖻', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝖮𝗇' if settings["imdb"] else '❌ 𝖮𝖿𝖿',
                                         callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝖲𝗉𝖾𝗅𝗅 𝖢𝗁𝖾𝖼𝗄',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝖮𝗇' if settings["spell_check"] else '❌ 𝖮𝖿𝖿',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝖶𝖾𝗅𝖼𝗈𝗆𝖾 𝖬𝖾𝗌𝗌𝖺𝗀𝖾', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝖮𝗇' if settings["welcome"] else '❌ 𝖮𝖿𝖿',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝖠𝗎𝗍𝗈 𝖣𝖾𝗅𝖾𝗍𝖾',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}'),
                    InlineKeyboardButton('5 𝖬𝗂𝗇' if settings["auto_delete"] else '❌ 𝖮𝖿𝖿',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝖠𝗎𝗍𝗈-𝖥𝗂𝗅𝗍𝖾𝗋',
                                         callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝖮𝗇' if settings["auto_ffilter"] else '❌ 𝖮𝖿𝖿',
                                         callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝖬𝖺𝗑 𝖡𝗎𝗍𝗍𝗈𝗇𝗌',
                                         callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(grp_id)}'),
                    InlineKeyboardButton('10' if settings["max_btn"] else f'{MAX_B_TN}',
                                         callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(grp_id)}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await client.send_message(
                chat_id=userid,
                text=f"<b>𝖢𝗁𝖺𝗇𝗀𝖾 𝖸𝗈𝗎𝗋 𝖲𝖾𝗍𝗍𝗂𝗇𝗀𝗌 𝖥𝗈𝗋 {title} 𝖠𝗌 𝖸𝗈𝗎𝗋 𝖶𝗂𝗌𝗁</b>",
                reply_markup=reply_markup,
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML,
                reply_to_message_id=query.message.id
            )

    elif query.data.startswith("show_option"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("⚠ 𝖴𝗇𝖺𝗏𝖺𝗂𝗅𝖺𝖻𝗅𝖾 ⚠", callback_data=f"unavailable#{from_user}"),
                InlineKeyboardButton("✅ 𝖴𝗉𝗅𝗈𝖺𝖽𝖾𝖽 ✅", callback_data=f"uploaded#{from_user}")
             ],[
                InlineKeyboardButton("🔰 𝖠𝗅𝗋𝖾𝖺𝖽𝗒 𝖠𝗏𝖺𝗂𝗅𝖺𝖻𝗅𝖾 🔰", callback_data=f"already_available#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton("❕ 𝖵𝗂𝖾𝗐 𝖲𝗍𝖺𝗍𝗎𝗌 ❕", url=f"https://t.me/+cXlkHDKryok0")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("𝖧𝖾𝗋𝖾 𝖺𝗋𝖾 𝗍𝗁𝖾 𝗈𝗉𝗍𝗂𝗈𝗇𝗌")
        else:
            await query.answer("𝖸𝗈𝗎 𝖽𝗈𝗇'𝗍 𝗁𝖺𝗏𝖾 𝗌𝗎𝖿𝖿𝗂𝖼𝗂𝖾𝗇𝗍 𝗋𝗂𝗀𝗁𝗍𝗌 𝗍𝗈 𝖽𝗈 𝗍𝗁𝗂𝗌 !", show_alert=True)
        
    elif query.data.startswith("unavailable"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("⚠ 𝖴𝗇𝖺𝗏𝖺𝗂𝗅𝖺𝖻𝗅𝖾 ⚠", callback_data=f"unalert#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton("❕ 𝖵𝗂𝖾𝗐 𝖲𝗍𝖺𝗍𝗎𝗌 ❕", url=f"https://t.me/+cXlkHDKryok0")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("𝖲𝖾𝗍 𝗍𝗈 𝖴𝗇𝖺𝗏𝖺𝗂𝗅𝖺𝖻𝗅𝖾")
            try:
                await client.send_message(chat_id=int(from_user), text=f"<b>𝖧𝖾𝗒 {user.mention}, 𝖲𝗈𝗋𝗋𝗒 𝗒𝗈𝗎𝗋 𝗋𝖾𝗊𝗎𝖾𝗌𝗍 𝗂𝗌 𝗎𝗇𝖺𝗏𝖺𝗂𝗅𝖺𝖻𝗅𝖾. 𝖲𝗈 𝗆𝗈𝖽𝖾𝗋𝖺𝗍𝗈𝗋𝗌 𝖼𝖺𝗇'𝗍 𝖺𝖽𝖽 𝗂𝗍 !</b>", reply_markup=InlineKeyboardMarkup(btn2))
            except UserIsBlocked:
                await client.send_message(chat_id=int(SUPPORT_CHAT_ID), text=f"<b>𝖧𝖾𝗒 {user.mention}, 𝖲𝗈𝗋𝗋𝗒 𝗒𝗈𝗎𝗋 𝗋𝖾𝗊𝗎𝖾𝗌𝗍 𝗂𝗌 𝗎𝗇𝖺𝗏𝖺𝗂𝗅𝖺𝖻𝗅𝖾. 𝖲𝗈 𝗆𝗈𝖽𝖾𝗋𝖺𝗍𝗈𝗋𝗌 𝖼𝖺𝗇'𝗍 𝖺𝖽𝖽 𝗂𝗍 !\n\n📝 𝖭𝗈𝗍𝖾: 𝖳𝗁𝗂𝗌 𝗆𝖾𝗌𝗌𝖺𝗀𝖾 𝗂𝗌 𝗌𝖾𝗇𝗍 𝗂𝗇 𝖦𝗋𝗈𝗎𝗉 𝖻𝖾𝖼𝖺𝗎𝗌𝖾 𝗒𝗈𝗎 𝗁𝖺𝗏𝖾 𝖡𝗅𝗈𝖼𝗄𝖾𝖽 𝗍𝗁𝖾 𝖡𝗈𝗍 ! 𝖴𝗇𝖻𝗅𝗈𝖼𝗄 𝗍𝗁𝖾 𝖡𝗈𝗍 !</b>", reply_markup=InlineKeyboardMarkup(btn2))
        else:
            await query.answer("𝖸𝗈𝗎 𝖽𝗈𝗇'𝗍 𝗁𝖺𝗏𝖾 𝗌𝗎𝖿𝖿𝗂𝖼𝗂𝖾𝗇𝗍 𝗋𝗂𝗀𝗁𝗍𝗌 𝗍𝗈 𝖽𝗈 𝗍𝗁𝗂𝗌 !", show_alert=True)

    elif query.data.startswith("uploaded"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("✅ 𝖴𝗉𝗅𝗈𝖺𝖽𝖾𝖽 ✅", callback_data=f"upalert#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton('𝐌𝐨𝐯𝐢𝐞 𝐒𝐞𝐚𝐫𝐜𝐡𝐢𝐧𝐠 𝐆𝐫𝐨𝐮𝐩', url="https://t.me/paxmovies")
               ],[
                 InlineKeyboardButton("❕ 𝖵𝗂𝖾𝗐 𝖲𝗍𝖺𝗍𝗎𝗌 ❕", url=f"https://t.me/+cXlkHDKryok0")
        ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("𝖲𝖾𝗍 𝗍𝗈 𝖴𝗉𝗅𝗈𝖺𝖽𝖾𝖽")
            try:
                await client.send_message(chat_id=int(from_user), text=f"<b>𝖧𝖾𝗒 {user.mention}, 𝖸𝗈𝗎𝗋 𝗋𝖾𝗊𝗎𝖾𝗌𝗍 𝗁𝖺𝗌 𝖻𝖾𝖾𝗇 𝗎𝗉𝗅𝗈𝖺𝖽𝖾𝖽 𝖻𝗒 𝗆𝗈𝖽𝖾𝗋𝖺𝗍𝗈𝗋. 𝖪𝗂𝗇𝖽𝗅𝗒 𝗌𝖾𝖺𝗋𝖼𝗁 𝖺𝗀𝖺𝗂𝗇 in Movies Request Groups !</b>", reply_markup=InlineKeyboardMarkup(btn2))
            except UserIsBlocked:
                await client.send_message(chat_id=int(SUPPORT_CHAT_ID), text=f"<b>𝖧𝖾𝗒 {user.mention}, 𝖸𝗈𝗎𝗋 𝗋𝖾𝗊𝗎𝖾𝗌𝗍 𝗁𝖺𝗌 𝖻𝖾𝖾𝗇 𝗎𝗉𝗅𝗈𝖺𝖽𝖾𝖽 𝖻𝗒 𝗆𝗈𝖽𝖾𝗋𝖺𝗍𝗈𝗋. 𝖪𝗂𝗇𝖽𝗅𝗒 𝗌𝖾𝖺𝗋𝖼𝗁 𝖺𝗀𝖺𝗂𝗇 in Movies Request Groups !\n\n📝 𝖭𝗈𝗍𝖾: 𝖳𝗁𝗂𝗌 𝗆𝖾𝗌𝗌𝖺𝗀𝖾 𝗂𝗌 𝗌𝖾𝗇𝗍 𝗂𝗇 𝖦𝗋𝗈𝗎𝗉 𝖻𝖾𝖼𝖺𝗎𝗌𝖾 𝗒𝗈𝗎 𝗁𝖺𝗏𝖾 𝖡𝗅𝗈𝖼𝗄𝖾𝖽 𝗍𝗁𝖾 𝖡𝗈𝗍 ! 𝖴𝗇𝖻𝗅𝗈𝖼𝗄 𝗍𝗁𝖾 𝖡𝗈𝗍 !</b>", reply_markup=InlineKeyboardMarkup(btn2))
        else:
            await query.answer("𝖸𝗈𝗎 𝖽𝗈𝗇'𝗍 𝗁𝖺𝗏𝖾 𝗌𝗎𝖿𝖿𝗂𝖼𝗂𝖾𝗇𝗍 𝗋𝗂𝗀𝗁𝗍𝗌 𝗍𝗈 𝖽𝗈 𝗍𝗁𝗂𝗌 !", show_alert=True)

    elif query.data.startswith("already_available"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("🔰 𝖠𝗅𝗋𝖾𝖺𝖽𝗒 𝖠𝗏𝖺𝗂𝗅𝖺𝖻𝗅𝖾 🔰", callback_data=f"alalert#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton('𝐌𝐨𝐯𝐢𝐞 𝐒𝐞𝐚𝐫𝐜𝐡𝐢𝐧𝐠 𝐆𝐫𝐨𝐮𝐩', url="https://t.me/paxmovies")
        ],[
                 InlineKeyboardButton("❕ 𝖵𝗂𝖾𝗐 𝖲𝗍𝖺𝗍𝗎𝗌 ❕", url=f"https://t.me/+cXlkHDKryok0")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("𝖲𝖾𝗍 𝗍𝗈 𝖺𝗅𝗋𝖾𝖺𝖽𝗒 𝖺𝗏𝖺𝗂𝗅𝖺𝖻𝗅𝖾 !")
            try:
                await client.send_message(chat_id=int(from_user), text=f"<b>𝖧𝖾𝗒 {user.mention}, 𝖸𝗈𝗎𝗋 𝗋𝖾𝗊𝗎𝖾𝗌𝗍 𝗂𝗌 𝖺𝗅𝗋𝖾𝖺𝖽𝗒 𝖺𝗏𝖺𝗂𝗅𝖺𝖻𝗅𝖾 𝗈𝗇 𝖡𝗈𝗍. 𝖪𝗂𝗇𝖽𝗅𝗒 𝗌𝖾𝖺𝗋𝖼𝗁 𝖺𝗀𝖺𝗂𝗇 in Movies Request Groups !</b>", reply_markup=InlineKeyboardMarkup(btn2))
            except UserIsBlocked:
                await client.send_message(chat_id=int(SUPPORT_CHAT_ID), text=f"<b>𝖧𝖾𝗒 {user.mention}, 𝖸𝗈𝗎𝗋 𝗋𝖾𝗊𝗎𝖾𝗌𝗍 𝗂𝗌 𝖺𝗅𝗋𝖾𝖺𝖽𝗒 𝖺𝗏𝖺𝗂𝗅𝖺𝖻𝗅𝖾 𝗈𝗇 𝖡𝗈𝗍. 𝖪𝗂𝗇𝖽𝗅𝗒 𝗌𝖾𝖺𝗋𝖼𝗁 𝖺𝗀𝖺𝗂𝗇 in Movies Request Groups !\n\n📝 𝖭𝗈𝗍𝖾: 𝖳𝗁𝗂𝗌 𝗆𝖾𝗌𝗌𝖺𝗀𝖾 𝗂𝗌 𝗌𝖾𝗇𝗍 𝗂𝗇 𝖦𝗋𝗈𝗎𝗉 𝖻𝖾𝖼𝖺𝗎𝗌𝖾 𝗒𝗈𝗎 𝗁𝖺𝗏𝖾 𝖡𝗅𝗈𝖼𝗄𝖾𝖽 𝗍𝗁𝖾 𝖡𝗈𝗍 ! 𝖴𝗇𝖻𝗅𝗈𝖼𝗄 𝗍𝗁𝖾 𝖡𝗈𝗍 !</b>", reply_markup=InlineKeyboardMarkup(btn2))
        else:
            await query.answer("𝖸𝗈𝗎 𝖽𝗈𝗇'𝗍 𝗁𝖺𝗏𝖾 𝗌𝗎𝖿𝖿𝗂𝖼𝗂𝖾𝗇𝗍 𝗋𝗂𝗀𝗁𝗍𝗌 𝗍𝗈 𝖽𝗈 𝗍𝗁𝗂𝗌 !", show_alert=True)

    elif query.data.startswith("alalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"𝖧𝖾𝗒 {user.first_name}, 𝖸𝗈𝗎𝗋 𝗋𝖾𝗊𝗎𝖾𝗌𝗍 𝗂𝗌 𝖺𝗅𝗋𝖾𝖺𝖽𝗒 𝖺𝗏𝖺𝗂𝗅𝖺𝖻𝗅𝖾 !", show_alert=True)
        else:
            await query.answer("𝖸𝗈𝗎 𝖽𝗈𝗇'𝗍 𝗁𝖺𝗏𝖾 𝗌𝗎𝖿𝖿𝗂𝖼𝗂𝖾𝗇𝗍 𝗋𝗂𝗀𝗁𝗍𝗌 𝗍𝗈 𝖽𝗈 𝗍𝗁𝗂𝗌 !", show_alert=True)

    elif query.data.startswith("upalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"𝖧𝖾𝗒 {user.first_name}, 𝖸𝗈𝗎𝗋 𝗋𝖾𝗊𝗎𝖾𝗌𝗍 𝗂𝗌 𝗎𝗉𝗅𝗈𝖺𝖽𝖾𝖽 !", show_alert=True)
        else:
            await query.answer("𝖸𝗈𝗎 𝖽𝗈𝗇'𝗍 𝗁𝖺𝗏𝖾 𝗌𝗎𝖿𝖿𝗂𝖼𝗂𝖾𝗇𝗍 𝗋𝗂𝗀𝗁𝗍𝗌 𝗍𝗈 𝖽𝗈 𝗍𝗁𝗂𝗌 !", show_alert=True)
        
    elif query.data.startswith("unalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"𝖧𝖾𝗒 {user.first_name}, 𝖸𝗈𝗎𝗋 𝗋𝖾𝗊𝗎𝖾𝗌𝗍 𝗂𝗌 𝖺𝗅𝗋𝖾𝖺𝖽𝗒 𝗎𝗇𝖺𝗏𝖺𝗂𝗅𝖺𝖻𝗅𝖾 !", show_alert=True)
        else:
            await query.answer("𝖸𝗈𝗎 𝖽𝗈𝗇'𝗍 𝗁𝖺𝗏𝖾 𝗌𝗎𝖿𝖿𝗂𝖼𝗂𝖾𝗇𝗍 𝗋𝗂𝗀𝗁𝗍𝗌 𝗍𝗈 𝖽𝗈 𝗍𝗁𝗂𝗌 !", show_alert=True)

    elif query.data == 'rkbtn':
        await query.answer("𝖧ᴇʏ 😍, \n\n🎯 Cʟɪᴄᴋ ᴀɴʏ ᴏғ ᴛʜᴇ ᴀʙᴏᴠᴇ Fɪʟᴇ ɴᴀᴍᴇs ᴛᴏ ɢᴇᴛ ɪᴛs Fɪʟᴇ ɪɴ ᴛʜᴇ BOT", True)

    elif query.data == 'tips':
        await query.answer("𝗥𝗲𝗾𝘂𝗲𝘀𝘁𝘀 𝗙𝗼𝗿𝗺𝗮𝘁𝘀\n\nMaster: Boss 2021 ❌ \nMaster Boss 2021 ✔️ \nSamdal-ri ❌ \nSamdal ri ✔️ \nArrow season 1 ❌ \nArrow S01 ✔️ \nBiggi episode 10 ❌ \nBiggi S01E10 ✔️ \n\nDᴏɴ'ᴛ ᴜsᴇ ᴀɴʏ ᴏғ ᴛʜᴇsᴇ ☞︎︎︎ :/([._-", True)
    
    elif query.data == 'info':
        await query.answer("I have reported to Admins.\n\n The movie will be added if available.\n\nYou will get a reply to your search message if added within 24 hours.\n Don't delete your message!", True)

    elif query.data == 'dupe':
        await query.answer("𝖥𝗂𝗅𝖾𝗌 𝖺𝗋𝖾 𝗍𝗁𝖾𝗋𝖾 𝗂𝗇 𝖻𝖾𝗅𝗈𝗐 𝖿𝗂𝗅𝗍𝖾𝗋 𝖡𝗎𝗍𝗍𝗈𝗇𝗌", True)

    elif query.data == "start":
        buttons = [[
                    InlineKeyboardButton('◦•●◉✿ ➕ ᴀᴅᴅ ᴍᴇ ᴛᴏ ɢʀᴏᴜᴘ ➕ ✿◉●•◦', url=f"http://t.me/{temp.U_NAME}?startgroup=true")
                ],[
                    InlineKeyboardButton('★⭕ ᴄʜᴀɴɴᴇʟ ⭕★', url="https://t.me/+cXlkHDKryok0"),
                    InlineKeyboardButton('★⭕ ᴅᴀɪʟʏ ᴜᴘᴅᴀᴛᴇs ⭕★', url=DAILY_UPDATE_LINK)
                ],[
                    InlineKeyboardButton('ᴍᴏᴠɪᴇ sᴇᴀʀᴄʜɪɴɢ ɢʀᴏᴜᴘ', url="https://t.me/paxmovies")
                ],[
                    InlineKeyboardButton('★♻️ ʜᴇʟᴘ ♻️★', callback_data='help'),
                    InlineKeyboardButton('★♻️ ᴀʙᴏᴜᴛ ♻️★', callback_data='about'),
                ]]
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer('↤↤↤↤↤ ᴄᴏɴsɪᴅᴇʀ ᴅᴏɴᴀᴛɪᴏɴ ↦↦↦↦↦')

    elif query.data == "filters":
        buttons = [[
            InlineKeyboardButton('✏ 𝖬𝖺𝗇𝗎𝖺𝗅 𝖥𝗂𝗅𝗍𝖾𝗋', callback_data='manuelfilter'),
            InlineKeyboardButton('📊 𝖠𝗎𝗍𝗈 𝖥𝗂𝗅𝗍𝖾𝗋', callback_data='autofilter')
        ],[
            InlineKeyboardButton('👩‍🦯 𝖡𝖺𝖼𝗄', callback_data='help'),
            InlineKeyboardButton('📈 𝖦𝗅𝗈𝖻𝖺𝗅 𝖥𝗂𝗅𝗍𝖾𝗋', callback_data='global_filters')
        ]]
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.ALL_FILTERS.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "global_filters":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝖡𝖺𝖼𝗄', callback_data='filters')
        ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.GFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    
    elif query.data == "help":
        buttons = [[
            InlineKeyboardButton('💼 𝖥𝗂𝗅𝗍𝖾𝗋𝗌 𝖬𝗈𝖽𝖾', callback_data='filters'),
            InlineKeyboardButton('🗂 𝖥𝗂𝗅𝖾 𝖲𝗍𝗈𝗋𝖾', callback_data='store_file')
        ], [
            InlineKeyboardButton('📟 𝖢𝗈𝗇𝗇𝖾𝖼𝗍𝗂𝗈𝗇𝗌', callback_data='coct'),
            InlineKeyboardButton('⚙ 𝖤𝗑𝗍𝗋𝖺 𝖬𝗈𝖽𝖾𝗌', callback_data='extra')
        ], [
            InlineKeyboardButton('🏘 𝖧𝗈𝗆𝖾', callback_data='start'),
            InlineKeyboardButton('♻️ Status', callback_data='stats')
        ]]
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.HELP_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "about":
        buttons = [[
            InlineKeyboardButton('🧬 𝖲𝗎𝗉𝗉𝗈𝗋𝗍 𝖦𝗋𝗈𝗎𝗉', url=f"https://t.me/{SUPPORT_CHAT}"),
            InlineKeyboardButton('📍 𝖲𝗈𝗎𝗋𝖼𝖾 𝖢𝗈𝖽𝖾', callback_data='source')
        ],[
            InlineKeyboardButton('🏘 𝖧𝗈𝗆𝖾', callback_data='start'),
            InlineKeyboardButton('❌ 𝖢𝗅𝗈𝗌𝖾', callback_data='close_data')
        ],[
            InlineKeyboardButton('👨‍💻 Contact Admin 👨‍💻', callback_data="owner_info")
                  ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "source":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝖡𝖺𝖼𝗄', callback_data='about')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.SOURCE_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "manuelfilter":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝖡𝖺𝖼𝗄', callback_data='filters'),
            InlineKeyboardButton('⏺ 𝖡𝗎𝗍𝗍𝗈𝗇𝗌', callback_data='button')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.MANUELFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "button":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝖡𝖺𝖼𝗄', callback_data='manuelfilter')
        ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.BUTTON_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "autofilter":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝖡𝖺𝖼𝗄', callback_data='filters')
        ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.AUTOFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "coct":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝖡𝖺𝖼𝗄', callback_data='help')
        ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.CONNECTION_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "extra":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝖡𝖺𝖼𝗄', callback_data='help'),
            InlineKeyboardButton('⚠ 𝖠𝖽𝗆𝗂𝗇', callback_data='admin')
        ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.EXTRAMOD_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    
    elif query.data == "store_file":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝖡𝖺𝖼𝗄', callback_data='help')
        ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.FILE_STORE_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    
    elif query.data == "admin":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝖡𝖺𝖼𝗄', callback_data='extra')
        ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ADMIN_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "stats":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝖡𝖺𝖼𝗄', callback_data='help'),
            InlineKeyboardButton('♻️ 𝖱𝖾𝖿𝗋𝖾𝗌𝗁', callback_data='rfrsh')
        ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit_text(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "rfrsh":
        await query.answer("Fetching MongoDb DataBase...")
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝖡𝖺𝖼𝗄', callback_data='help'),
            InlineKeyboardButton('♻️ 𝖱𝖾𝖿𝗋𝖾𝗌𝗁', callback_data='rfrsh')
        ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit_text(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "owner_info":
            btn = [[
                    InlineKeyboardButton("👩‍🦯 𝖡𝖺𝖼𝗄", callback_data="start"),
                    InlineKeyboardButton("📞 𝖢𝗈𝗇𝗍𝖺𝖼𝗍", url=f"https://telegram.me/Mr_John_NigMore")
                  ]]
            await client.edit_message_media(
                query.message.chat.id, 
                query.message.id, 
                InputMediaPhoto(random.choice(PICS))
            )
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_text(
                text=(script.OWNER_INFO),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            )

    elif query.data.startswith("setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        grpid = await active_connection(str(query.from_user.id))

        if str(grp_id) != str(grpid):
            await query.message.edit("Your Active Connection Has Been Changed. Go To /settings.")
            return await query.answer('♻️ Please Share and Support ♻️')

        if status == "True":
            await save_group_settings(grpid, set_type, False)
        else:
            await save_group_settings(grpid, set_type, True)

        settings = await get_settings(grpid)

        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('𝖥𝗂𝗅𝗍𝖾𝗋 𝖡𝗎𝗍𝗍𝗈𝗇',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}'),
                    InlineKeyboardButton('𝖲𝗂𝗇𝗀𝗅𝖾 𝖡𝗎𝗍𝗍𝗈𝗇' if settings["button"] else '𝖣𝗈𝗎𝖻𝗅𝖾',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝖥𝗂𝗅𝖾 𝖲𝖾𝗇𝖽 𝖬𝗈𝖽𝖾', callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}'),
                    InlineKeyboardButton('𝖬𝖺𝗇𝗎𝖺𝗅 𝖲𝗍𝖺𝗋𝗍' if settings["botpm"] else '𝖠𝗎𝗍𝗈 𝖲𝖾𝗇𝖽',
                                         callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝖯𝗋𝗈𝗍𝖾𝖼𝗍 𝖢𝗈𝗇𝗍𝖾𝗇𝗍',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝖮𝗇' if settings["file_secure"] else '❌ 𝖮𝖿𝖿',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝖨𝖬𝖣𝖻', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝖮𝗇' if settings["imdb"] else '❌ 𝖮𝖿𝖿',
                                         callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝖲𝗉𝖾𝗅𝗅 𝖢𝗁𝖾𝖼𝗄',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝖮𝗇' if settings["spell_check"] else '❌ 𝖮𝖿𝖿',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝖶𝖾𝗅𝖼𝗈𝗆𝖾 𝖬𝖾𝗌𝗌𝖺𝗀𝖾', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝖮𝗇' if settings["welcome"] else '❌ 𝖮𝖿𝖿',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝖠𝗎𝗍𝗈 𝖣𝖾𝗅𝖾𝗍𝖾',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}'),
                    InlineKeyboardButton('5 𝖬𝗂𝗇' if settings["auto_delete"] else '❌ 𝖮𝖿𝖿',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝖠𝗎𝗍𝗈-𝖥𝗂𝗅𝗍𝖾𝗋',
                                         callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝖮𝗇' if settings["auto_ffilter"] else '❌ 𝖮𝖿𝖿',
                                         callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝖬𝖺𝗑 𝖡𝗎𝗍𝗍𝗈𝗇𝗌',
                                         callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(grp_id)}'),
                    InlineKeyboardButton('10' if settings["max_btn"] else f'{MAX_B_TN}',
                                         callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(grp_id)}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_reply_markup(reply_markup)
    await query.answer('♻️ Please Share and Support ♻️')

    
async def auto_filter(client, msg, spoll=False):
    reqstr1 = msg.from_user.id if msg.from_user else 0
    reqstr = await client.get_users(reqstr1)
    if not spoll:
        if msg.text.startswith("/"):
            return
        try:
            gchat_id = int(msg.chat.id)
            chat_info = await client.get_chat(gchat_id)
            await send_react(chat_info, msg)
        except:
            pass
        stick = await msg.reply_sticker(sticker="CAACAgQAAxkBAdumNGfK4Rcgb3VPtirCHpiZTsf8fExbAAKmDwACdo5YU0nvPPPp_97lNgQ")
        message = msg
        settings = await get_settings(message.chat.id)
        if re.findall(r"((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            await stick.delete()
            return
        if len(message.text) < 100:
            search = message.text
            search = search.lower()
            find = search.split(" ")
            search = ""
            removes = ["upload", "series", "horror", "thriller", "print", "file", "movie", "dub", "download"]
            for x in find:
                if x in removes:
                    continue
                else:
                    search = search + x + " "
            search = re.sub(r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|gib)(\sme)?)|movie(s)?|latest)", "", search, flags=re.IGNORECASE)
            search = re.sub(r"\s+", " ", search).strip()
            search = search.replace("-", " ")
            search = search.replace("_", " ")
            search = search.replace(":", "")
            search = search.replace(".", "")
            files, offset, total_results = await get_search_results(message.chat.id ,search, offset=0, filter=True)
            settings = await get_settings(message.chat.id)
            if not files:
                if settings["spell_check"]:
                    await stick.delete()
                    return await advantage_spell_chok(client, msg)
                else:
                    await stick.delete()
                    return
        else:
            await stick.delete()
            return
    else:
        message = msg.message.reply_to_message  # msg will be callback query
        search, files, offset, total_results = spoll
        settings = await get_settings(msg.message.chat.id)
        
    key = f"{message.chat.id}-{message.id}"
    temp.FILES_IDS[key] = files
    pre = 'filep' if settings['file_secure'] else 'file'
    req = message.from_user.id if message.from_user else 0
    BUTTONS[key] = search
    files_link = ""
    end_cap = ""
    
    if settings["button"]:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"📂{get_size(file.file_size)} 🎥{file.file_name}", callback_data=f'{pre}#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = []
        end_cap = f"""© @paxtv"""
        for file in files:
            # files_link += f"""\n<blockquote><b>🎬 𝐅𝐢𝐥𝐞: <a href=https://t.me/{temp.U_NAME}?start={pre}_{file.file_id}>{file.file_name}</a></blockquote>\n📁 𝐒𝐢𝐳𝐞: {get_size(file.file_size)}</b>\n"""
            files_link += f"<b>📁 {get_size(file.file_size)} <a href=https://t.me/{temp.U_NAME}?start={pre}_{file.file_id}> ▷ {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file.file_name.split()))}\n\n</a></b>"
            # files_link += f"<b><a href='https://t.me/{temp.U_NAME}?start={pre}_{file.file_id}'> 📁 {get_size(file.file_size)} ▷ {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file.file_name.split()))}\n\n</a></b>"

            

    try:
        if settings['button']:
            btn.insert(0, 
            [
                InlineKeyboardButton(f'📟 𝖥𝗂𝗅𝖾𝗌: {len(files)}', 'dupe'),
                InlineKeyboardButton(f'📮 Info', 'tips'),
                InlineKeyboardButton(f'🎁 𝖳𝗂𝗉𝗌', 'info')
            ]
            )
                
    except KeyError:
        grpid = await active_connection(str(message.from_user.id))
        await save_group_settings(grpid, 'auto_delete', True)
        settings = await get_settings(message.chat.id)
        if settings['button']:
            btn.insert(0, 
            [
                InlineKeyboardButton(f'📟 𝖥𝗂𝗅𝖾𝗌: {len(files)}', 'dupe'),
                InlineKeyboardButton(f'📮 Info', 'tips'),
                InlineKeyboardButton(f'🎁 𝖳𝗂𝗉𝗌', 'info')
            ]
            )

            
    btn.insert(0,
               [
                   InlineKeyboardButton("Lᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}#{req}#{offset}"),
                   InlineKeyboardButton("Sᴇᴀsᴏɴ", callback_data=f"seasons#{key}#{req}#{offset}"),
                   InlineKeyboardButton("Qᴜᴀʟɪᴛʏ", callback_data=f"qualities#{key}#{req}#{offset}")
               ]
              )
    if settings['button']:
        btn.insert(0, [
            InlineKeyboardButton(f'🎬 {search} 🎬', 'rkbtn')
        ])
    
    
    if offset != "":
        try:
            settings = await get_settings(message.chat.id)
            if settings['max_btn']:
                btn.append(
                    [InlineKeyboardButton("📃", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="𝖭𝖤𝖷𝖳 ▶️",callback_data=f"next_{req}_{key}_{offset}")]
                )
            else:
                btn.append(
                    [InlineKeyboardButton("📃", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/int(MAX_B_TN))}",callback_data="pages"), InlineKeyboardButton(text="𝖭𝖤𝖷𝖳 ▶️",callback_data=f"next_{req}_{key}_{offset}")]
                )
        except KeyError:
            await save_group_settings(message.chat.id, 'max_btn', False)
            settings = await get_settings(message.chat.id)
            if settings['max_btn']:
                btn.append(
                    [InlineKeyboardButton("📃", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="𝖭𝖤𝖷𝖳 ▶️",callback_data=f"next_{req}_{key}_{offset}")]
                )
            else:
                btn.append(
                    [InlineKeyboardButton("📃", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/int(MAX_B_TN))}",callback_data="pages"), InlineKeyboardButton(text="𝖭𝖤𝖷𝖳 ▶️",callback_data=f"next_{req}_{key}_{offset}")]
                )
    else:
        btn.append(
            [InlineKeyboardButton(text="🚸 Nᴏ ᴍᴏʀᴇ Pᴀɢᴇs 🚸",callback_data="pages")]
        )
    imdb = await get_poster(search, file=(files[0]).file_name) if settings["imdb"] else None
    TEMPLATE = settings['template']
    if imdb:
        cap = TEMPLATE.format(
            query=search,
            title=imdb['title'],
            votes=imdb['votes'],
            aka=imdb["aka"],
            seasons=imdb["seasons"],
            box_office=imdb['box_office'],
            localized_title=imdb['localized_title'],
            kind=imdb['kind'],
            imdb_id=imdb["imdb_id"],
            cast=imdb["cast"],
            runtime=imdb["runtime"],
            countries=imdb["countries"],
            certificates=imdb["certificates"],
            languages=imdb["languages"],
            director=imdb["director"],
            writer=imdb["writer"],
            producer=imdb["producer"],
            composer=imdb["composer"],
            cinematographer=imdb["cinematographer"],
            music_team=imdb["music_team"],
            distributors=imdb["distributors"],
            release_date=imdb['release_date'],
            year=imdb['year'],
            genres=imdb['genres'],
            poster=imdb['poster'],
            plot=imdb['plot'],
            rating=imdb['rating'],
            url=imdb['url'],
            **locals()
        )
    else:
        cap = f"<b>🧿 ᴛɪᴛʟᴇ : <code>{search}</code>\n📂 ᴛᴏᴛᴀʟ ꜰɪʟᴇꜱ : <code>{total_results}</code>\n📝 ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ : {message.from_user.mention}\n⚜️ ᴘᴏᴡᴇʀᴇᴅ ʙʏ : 👇\n⚡ {message.chat.title} \n\n</b>"
    CAP[key] = cap
    if imdb and imdb.get('poster'):
        try:
            if not spoll:
                await stick.delete()
            hehe = await message.reply_photo(photo=imdb.get('poster'), caption=cap[:1024] + files_link + end_cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)
            try:
                if settings['auto_delete']:
                    await asyncio.sleep(300)
                    await hehe.delete()
                    await message.delete()
            except KeyError:
                grpid = await active_connection(str(message.from_user.id))
                await save_group_settings(grpid, 'auto_delete', True)
                settings = await get_settings(message.chat.id)
                if settings['auto_delete']:
                    await asyncio.sleep(300)
                    await hehe.delete()
                    await message.delete()
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            pic = imdb.get('poster')
            poster = pic.replace('.jpg', "._V1_UX360.jpg")
            if not spoll:
                await stick.delete()
            hmm = await message.reply_photo(photo=poster, caption=cap[:1024] + files_link + end_cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)
            try:
                if settings['auto_delete']:
                    await asyncio.sleep(300)
                    await hmm.delete()
                    await message.delete()
            except KeyError:
                grpid = await active_connection(str(message.from_user.id))
                await save_group_settings(grpid, 'auto_delete', True)
                settings = await get_settings(message.chat.id)
                if settings['auto_delete']:
                    await asyncio.sleep(300)
                    await hmm.delete()
                    await message.delete()
        except Exception as e:
            logger.exception(e)
            if not spoll:
                await stick.delete()
            fek = await message.reply_photo(photo=NOR_IMG, caption=cap + files_link + end_cap, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)
            try:
                if settings['auto_delete']:
                    await asyncio.sleep(300)
                    await fek.delete()
                    await message.delete()
            except KeyError:
                grpid = await active_connection(str(message.from_user.id))
                await save_group_settings(grpid, 'auto_delete', True)
                settings = await get_settings(message.chat.id)
                if settings['auto_delete']:
                    await asyncio.sleep(300)
                    await fek.delete()
                    await message.delete()
    else:
        if not spoll:
                await stick.delete()
        fuk = await message.reply_text(text=cap + files_link + end_cap, reply_markup=InlineKeyboardMarkup(btn), protect_content=False, parse_mode=enums.ParseMode.HTML)
        try:
            if settings['auto_delete']:
                await asyncio.sleep(300)
                await fuk.delete()
                await message.delete()
        except KeyError:
            grpid = await active_connection(str(message.from_user.id))
            await save_group_settings(grpid, 'auto_delete', True)
            settings = await get_settings(message.chat.id)
            if settings['auto_delete']:
                await asyncio.sleep(300)
                await fuk.delete()
                await message.delete()
    if spoll:
        await msg.message.delete()

async def advantage_spell_chok(client, message):
    search = message.text
    google_search = search.replace(" ", "+")
    encoded_search = quote(search)
    button = [[
        InlineKeyboardButton("🔎 Sᴇᴀʀᴄʜ ɪɴ Gᴏᴏɢʟᴇ 🔍", url=f"https://www.google.com/search?q={google_search}")
    ]]
    query = re.sub(
        r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|gib)(\sme)?)|season|episode|movie(s)?|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|dub(b)?ed|file)",
        "", search, flags=re.IGNORECASE)  # pls contribute some common words
    query = query.strip()
    try:
        movies = await get_poster(query, bulk=True)
    except:
        n = await message.reply_photo(
            photo=SPELL_IMG, 
            caption=script.I_CUDNT.format(search),
            reply_markup=InlineKeyboardMarkup(button)
        )
        await asyncio.sleep(60)
        await n.delete()
        #try:
            #await message.delete()
        #except:
            #pass
        return

    if not movies:
        n = await message.reply_photo(
            photo=SPELL_IMG, 
            caption=script.I_CUDNT.format(search),
            reply_markup=InlineKeyboardMarkup(button)
        )
        await asyncio.sleep(60)
        await n.delete()
        #try:
            #await message.delete()
        #except:
            #pass
        return

    user = message.from_user.id if message.from_user else 0
    movielist = []
    if len(movies) > 5:
        movies = movies[:5]
    for mov in movies:
        movielist.append(mov.get('title'))
    movielist = list(dict.fromkeys(movielist))
    if not movielist:
        n = await message.reply_photo(
            photo=SPELL_IMG, 
            caption=script.I_CUDNT.format(search),
            reply_markup=InlineKeyboardMarkup(button)
        )
        await asyncio.sleep(60)
        await n.delete()
        #try:
            #await message.delete()
        #except:
            #pass
        return

    valid_movies = [movie for movie in movielist if len(f"spolling#{user}#{movie}") <= 64]
    
    if not valid_movies:
        n = await message.reply_photo(
            photo=SPELL_IMG, 
            caption=script.I_CUDNT.format(search),
            reply_markup=InlineKeyboardMarkup(button)
        )
        await asyncio.sleep(60)
        await n.delete()
        #try:
            #await message.delete()
        #except:
            #pass
        return

    buttons = []
    for movie in valid_movies:
        callback_data = f"spolling#{user}#{movie}"
        buttons.append([InlineKeyboardButton(text=movie.strip(), callback_data=callback_data)])

    buttons.append([InlineKeyboardButton("🚫 ᴄʟᴏsᴇ 🚫", callback_data="close_data")])

    s = await message.reply_photo(
        photo=SPELL_IMG,
        caption=script.CUDNT_FND.format(search),
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    await asyncio.sleep(300)
    await s.delete()
    #try:
        #await message.delete()
    #except:
        #pass    

async def manual_filters(client, message, text=False):
    settings = await get_settings(message.chat.id)
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_filters(group_id)
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_filter(group_id, keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            piroxrk = await client.send_message(
                                group_id, 
                                reply_text, 
                                disable_web_page_preview=True,
                                protect_content=True if settings["file_secure"] else False,
                                reply_to_message_id=reply_id
                            )
                            try:
                                if settings['auto_ffilter']:
                                    await auto_filter(client, message)
                                    try:
                                        if settings['auto_delete']:
                                            await asyncio.sleep(300)
                                            await piroxrk.delete()
                                    except KeyError:
                                        grpid = await active_connection(str(message.from_user.id))
                                        await save_group_settings(grpid, 'auto_delete', True)
                                        settings = await get_settings(message.chat.id)
                                        if settings['auto_delete']:
                                            await asyncio.sleep(300)
                                            await piroxrk.delete()
                                else:
                                    try:
                                        if settings['auto_delete']:
                                            await asyncio.sleep(300)
                                            await piroxrk.delete()
                                    except KeyError:
                                        grpid = await active_connection(str(message.from_user.id))
                                        await save_group_settings(grpid, 'auto_delete', True)
                                        settings = await get_settings(message.chat.id)
                                        if settings['auto_delete']:
                                            await asyncio.sleep(300)
                                            await piroxrk.delete()
                            except KeyError:
                                grpid = await active_connection(str(message.from_user.id))
                                await save_group_settings(grpid, 'auto_ffilter', True)
                                settings = await get_settings(message.chat.id)
                                if settings['auto_ffilter']:
                                    await auto_filter(client, message)

                        else:
                            button = eval(btn)
                            piroxrk = await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                protect_content=True if settings["file_secure"] else False,
                                reply_to_message_id=reply_id
                            )
                            try:
                                if settings['auto_ffilter']:
                                    await auto_filter(client, message)
                                    try:
                                        if settings['auto_delete']:
                                            await asyncio.sleep(300)
                                            await piroxrk.delete()
                                    except KeyError:
                                        grpid = await active_connection(str(message.from_user.id))
                                        await save_group_settings(grpid, 'auto_delete', True)
                                        settings = await get_settings(message.chat.id)
                                        if settings['auto_delete']:
                                            await asyncio.sleep(300)
                                            await piroxrk.delete()
                                else:
                                    try:
                                        if settings['auto_delete']:
                                            await asyncio.sleep(300)
                                            await piroxrk.delete()
                                    except KeyError:
                                        grpid = await active_connection(str(message.from_user.id))
                                        await save_group_settings(grpid, 'auto_delete', True)
                                        settings = await get_settings(message.chat.id)
                                        if settings['auto_delete']:
                                            await asyncio.sleep(300)
                                            await piroxrk.delete()
                            except KeyError:
                                grpid = await active_connection(str(message.from_user.id))
                                await save_group_settings(grpid, 'auto_ffilter', True)
                                settings = await get_settings(message.chat.id)
                                if settings['auto_ffilter']:
                                    await auto_filter(client, message)

                    elif btn == "[]":
                        piroxrk = await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            protect_content=True if settings["file_secure"] else False,
                            reply_to_message_id=reply_id
                        )
                        try:
                            if settings['auto_ffilter']:
                                await auto_filter(client, message)
                                try:
                                    if settings['auto_delete']:
                                        await asyncio.sleep(300)
                                        await piroxrk.delete()
                                except KeyError:
                                    grpid = await active_connection(str(message.from_user.id))
                                    await save_group_settings(grpid, 'auto_delete', True)
                                    settings = await get_settings(message.chat.id)
                                    if settings['auto_delete']:
                                        await asyncio.sleep(300)
                                        await piroxrk.delete()
                            else:
                                try:
                                    if settings['auto_delete']:
                                        await asyncio.sleep(300)
                                        await piroxrk.delete()
                                except KeyError:
                                    grpid = await active_connection(str(message.from_user.id))
                                    await save_group_settings(grpid, 'auto_delete', True)
                                    settings = await get_settings(message.chat.id)
                                    if settings['auto_delete']:
                                        await asyncio.sleep(300)
                                        await piroxrk.delete()
                        except KeyError:
                            grpid = await active_connection(str(message.from_user.id))
                            await save_group_settings(grpid, 'auto_ffilter', True)
                            settings = await get_settings(message.chat.id)
                            if settings['auto_ffilter']:
                                await auto_filter(client, message)

                    else:
                        button = eval(btn)
                        piroxrk = await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )
                        try:
                            if settings['auto_ffilter']:
                                await auto_filter(client, message)
                                try:
                                    if settings['auto_delete']:
                                        await asyncio.sleep(300)
                                        await piroxrk.delete()
                                except KeyError:
                                    grpid = await active_connection(str(message.from_user.id))
                                    await save_group_settings(grpid, 'auto_delete', True)
                                    settings = await get_settings(message.chat.id)
                                    if settings['auto_delete']:
                                        await asyncio.sleep(300)
                                        await piroxrk.delete()
                            else:
                                try:
                                    if settings['auto_delete']:
                                        await asyncio.sleep(300)
                                        await piroxrk.delete()
                                except KeyError:
                                    grpid = await active_connection(str(message.from_user.id))
                                    await save_group_settings(grpid, 'auto_delete', True)
                                    settings = await get_settings(message.chat.id)
                                    if settings['auto_delete']:
                                        await asyncio.sleep(300)
                                        await piroxrk.delete()
                        except KeyError:
                            grpid = await active_connection(str(message.from_user.id))
                            await save_group_settings(grpid, 'auto_ffilter', True)
                            settings = await get_settings(message.chat.id)
                            if settings['auto_ffilter']:
                                await auto_filter(client, message)

                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False

async def global_filters(client, message, text=False):
    settings = await get_settings(message.chat.id)
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_gfilters('gfilters')
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_gfilter('gfilters', keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            joelkb = await client.send_message(
                                group_id, 
                                reply_text, 
                                disable_web_page_preview=True,
                                reply_to_message_id=reply_id
                            )
                            manual = await manual_filters(client, message)
                            if manual == False:
                                settings = await get_settings(message.chat.id)
                                try:
                                    if settings['auto_ffilter']:
                                        await auto_filter(client, message)
                                        try:
                                            if settings['spell_check']:
                                                await joelkb.delete()
                                        except KeyError:
                                            grpid = await active_connection(str(message.from_user.id))
                                            await save_group_settings(grpid, 'auto_delete', True)
                                            settings = await get_settings(message.chat.id)
                                            if settings['spell_check']:
                                                await joelkb.delete()
                                    else:
                                        try:
                                            if settings['spell_check']:
                                                await asyncio.sleep(120)
                                                await joelkb.delete()
                                        except KeyError:
                                            grpid = await active_connection(str(message.from_user.id))
                                            await save_group_settings(grpid, 'auto_delete', True)
                                            settings = await get_settings(message.chat.id)
                                            if settings['spell_check']:
                                                await asyncio.sleep(120)
                                                await joelkb.delete()
                                except KeyError:
                                    grpid = await active_connection(str(message.from_user.id))
                                    await save_group_settings(grpid, 'auto_ffilter', True)
                                    settings = await get_settings(message.chat.id)
                                    if settings['auto_ffilter']:
                                        await auto_filter(client, message) 
                            else:
                                try:
                                    if settings['spell_check']:
                                        await joelkb.delete()
                                except KeyError:
                                    grpid = await active_connection(str(message.from_user.id))
                                    await save_group_settings(grpid, 'auto_delete', True)
                                    settings = await get_settings(message.chat.id)
                                    if settings['spell_check']:
                                        await joelkb.delete()
                            
                        else:
                            button = eval(btn)
                            joelkb = await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id=reply_id
                            )
                            manual = await manual_filters(client, message)
                            if manual == False:
                                settings = await get_settings(message.chat.id)
                                try:
                                    if settings['auto_ffilter']:
                                        await auto_filter(client, message)
                                        try:
                                            if settings['spell_check']:
                                                await joelkb.delete()
                                        except KeyError:
                                            grpid = await active_connection(str(message.from_user.id))
                                            await save_group_settings(grpid, 'auto_delete', True)
                                            settings = await get_settings(message.chat.id)
                                            if settings['spell_check']:
                                                await joelkb.delete()
                                    else:
                                        try:
                                            if settings['spell_check']:
                                                await asyncio.sleep(120)
                                                await joelkb.delete()
                                        except KeyError:
                                            grpid = await active_connection(str(message.from_user.id))
                                            await save_group_settings(grpid, 'auto_delete', True)
                                            settings = await get_settings(message.chat.id)
                                            if settings['spell_check']:
                                                await asyncio.sleep(120)
                                                await joelkb.delete()
                                except KeyError:
                                    grpid = await active_connection(str(message.from_user.id))
                                    await save_group_settings(grpid, 'auto_ffilter', True)
                                    settings = await get_settings(message.chat.id)
                                    if settings['auto_ffilter']:
                                        await auto_filter(client, message) 
                            else:
                                try:
                                    if settings['spell_check']:
                                        await joelkb.delete()
                                except KeyError:
                                    grpid = await active_connection(str(message.from_user.id))
                                    await save_group_settings(grpid, 'auto_delete', True)
                                    settings = await get_settings(message.chat.id)
                                    if settings['spell_check']:
                                        await joelkb.delete()

                    elif btn == "[]":
                        joelkb = await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            reply_to_message_id=reply_id
                        )
                        manual = await manual_filters(client, message)
                        if manual == False:
                            settings = await get_settings(message.chat.id)
                            try:
                                if settings['auto_ffilter']:
                                    await auto_filter(client, message)
                                    try:
                                        if settings['spell_check']:
                                            await joelkb.delete()
                                    except KeyError:
                                        grpid = await active_connection(str(message.from_user.id))
                                        await save_group_settings(grpid, 'auto_delete', True)
                                        settings = await get_settings(message.chat.id)
                                        if settings['spell_check']:
                                            await joelkb.delete()
                                else:
                                    try:
                                        if settings['spell_check']:
                                            await asyncio.sleep(120)
                                            await joelkb.delete()
                                    except KeyError:
                                        grpid = await active_connection(str(message.from_user.id))
                                        await save_group_settings(grpid, 'auto_delete', True)
                                        settings = await get_settings(message.chat.id)
                                        if settings['spell_check']:
                                            await asyncio.sleep(120)
                                            await joelkb.delete()
                            except KeyError:
                                grpid = await active_connection(str(message.from_user.id))
                                await save_group_settings(grpid, 'auto_ffilter', True)
                                settings = await get_settings(message.chat.id)
                                if settings['auto_ffilter']:
                                    await auto_filter(client, message) 
                        else:
                            try:
                                if settings['spell_check']:
                                    await joelkb.delete()
                            except KeyError:
                                grpid = await active_connection(str(message.from_user.id))
                                await save_group_settings(grpid, 'auto_delete', True)
                                settings = await get_settings(message.chat.id)
                                if settings['spell_check']:
                                    await joelkb.delete()

                    else:
                        button = eval(btn)
                        joelkb = await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )
                        manual = await manual_filters(client, message)
                        if manual == False:
                            settings = await get_settings(message.chat.id)
                            try:
                                if settings['auto_ffilter']:
                                    await auto_filter(client, message)
                                    try:
                                        if settings['spell_check']:
                                            await joelkb.delete()
                                    except KeyError:
                                        grpid = await active_connection(str(message.from_user.id))
                                        await save_group_settings(grpid, 'auto_delete', True)
                                        settings = await get_settings(message.chat.id)
                                        if settings['spell_check']:
                                            await joelkb.delete()
                                else:
                                    try:
                                        if settings['spell_check']:
                                            await asyncio.sleep(120)
                                            await joelkb.delete()
                                    except KeyError:
                                        grpid = await active_connection(str(message.from_user.id))
                                        await save_group_settings(grpid, 'auto_delete', True)
                                        settings = await get_settings(message.chat.id)
                                        if settings['spell_check']:
                                            await asyncio.sleep(120)
                                            await joelkb.delete()
                            except KeyError:
                                grpid = await active_connection(str(message.from_user.id))
                                await save_group_settings(grpid, 'auto_ffilter', True)
                                settings = await get_settings(message.chat.id)
                                if settings['auto_ffilter']:
                                    await auto_filter(client, message) 
                        else:
                            try:
                                if settings['spell_check']:
                                    await joelkb.delete()
                            except KeyError:
                                grpid = await active_connection(str(message.from_user.id))
                                await save_group_settings(grpid, 'auto_delete', True)
                                settings = await get_settings(message.chat.id)
                                if settings['spell_check']:
                                    await joelkb.delete()

                                
                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False
