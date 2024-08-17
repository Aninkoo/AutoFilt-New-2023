import os
import math
import logging
import random, string
import asyncio
import time
from Script import script
from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.ia_filterdb import Media, get_file_details, unpack_new_file_id, get_bad_files, get_search_results
from database.users_chats_db import db
from info import CHANNELS, ADMINS, AUTH_CHANNEL, IS_VERIFY, VERIFY_EXPIRE, SHORTLINK_API, SHORTLINK_URL, LOG_CHANNEL, PICS, BATCH_FILE_CAPTION, CUSTOM_FILE_CAPTION, DAILY_UPDATE_LINK, SUPPORT_CHAT, PROTECT_CONTENT, REQST_CHANNEL, SUPPORT_CHAT_ID, MAX_B_TN, NOR_IMG
from utils import get_settings, get_size, get_shortlink, get_verify_status, update_verify_status, is_subscribed, get_readable_time, save_group_settings, temp
from database.connections_mdb import active_connection
import re
from datetime import datetime, timedelta, timezone
from plugins.pm_filter import BUTTONS, CAP
import json
import pytz
import base64
from telegraph import upload_file

logger = logging.getLogger(__name__)

BATCH_FILES = {}

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        buttons = [[
                    InlineKeyboardButton('★⭕ ᴄʜᴀɴɴᴇʟ ⭕★', url="https://t.me/isaimini_updates"),
                    InlineKeyboardButton('★⭕ ᴅᴀɪʟʏ ᴜᴘᴅᴀᴛᴇs ⭕★', url=DAILY_UPDATE_LINK)
                ],[
                    InlineKeyboardButton('★♻️ ʜᴇʟᴘ ♻️★', callback_data='help'),
                    InlineKeyboardButton('★♻️ ᴀʙᴏᴜᴛ ♻️★', callback_data='about'),
                ],[
                    InlineKeyboardButton('◦•●◉✿ ✅ ᴅᴏɴᴀᴛᴇ ᴍᴇ ✅ ✿◉●•◦', url='https://t.me/isaimini_donation/5')
                  ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            quote=True,
            parse_mode=enums.ParseMode.HTML
        )
        await asyncio.sleep(2)
        if not await db.get_chat(message.chat.id):
            total=await client.get_chat_members_count(message.chat.id)
            await client.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(message.chat.title, message.chat.id, total, "Unknown"))       
            await db.add_chat(message.chat.id, message.chat.title)
        return 
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(message.from_user.id, message.from_user.mention))

    verify_status = await get_verify_status(message.from_user.id)
    if verify_status['is_verified'] and VERIFY_EXPIRE < (time.time() - verify_status['verified_time']):
        await update_verify_status(message.from_user.id, is_verified=False)

    t_z = pytz.timezone('Asia/Kolkata')
    t_now = datetime.now(t_z)
    verify_expire_time = t_now + timedelta(seconds=VERIFY_EXPIRE)
    next_verify_str = verify_expire_time.strftime("%H:%M:%S %p")
    
    if len(message.command) != 2 or (len(message.command) == 2 and message.command[1] == 'start'):
        buttons = [[
                    InlineKeyboardButton('◦•●◉✿ ➕ ᴀᴅᴅ ᴍᴇ ᴛᴏ ɢʀᴏᴜᴘ ➕ ✿◉●•◦', url=f"http://t.me/{temp.U_NAME}?startgroup=true")
                ],[
                    InlineKeyboardButton('★⭕ ᴄʜᴀɴɴᴇʟ ⭕★', url="https://t.me/isaimini_updates"),
                    InlineKeyboardButton('★⭕ ᴅᴀɪʟʏ ᴜᴘᴅᴀᴛᴇs ⭕★', url=DAILY_UPDATE_LINK)
                ],[
                    InlineKeyboardButton(']|I{•---» ᴍᴏᴠɪᴇ sᴇᴀʀᴄʜɪɴɢ ɢʀᴏᴜᴘ ʟɪɴᴋs «---•}I|[', url="https://t.me/isaimini_updates/110")
                ],[
                    InlineKeyboardButton('★♻️ ʜᴇʟᴘ ♻️★', callback_data='help'),
                    InlineKeyboardButton('★♻️ ᴀʙᴏᴜᴛ ♻️★', callback_data='about'),
                ],[
                    InlineKeyboardButton('◦•●◉✿ ✅ ᴅᴏɴᴀᴛᴇ ᴍᴇ ✅ ✿◉●•◦', url='https://t.me/isaimini_donation/5')
                  ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            quote=True,
            parse_mode=enums.ParseMode.HTML
        )
        return
    if AUTH_CHANNEL and not await is_subscribed(client, message):
        try:
            invite_link = await client.create_chat_invite_link(int(AUTH_CHANNEL))
        except ChatAdminRequired:
            logger.error("Make sure Bot is admin in Forcesub channel")
            return
        btn = [
            [
                InlineKeyboardButton(
                    "🤖 𝖩𝗈𝗂𝗇 𝖴𝗉𝖽𝖺𝗍𝖾𝗌 𝖢𝗁𝖺𝗇𝗇𝖾𝗅 🤖", url=invite_link.invite_link
                )
            ]
        ]

        if message.command[1] != "subscribe" or message.command[1] != "send_all":
            try:
                kk, file_id = message.command[1].split("_", 1)
                pre = 'checksubp' if kk == 'filep' else 'checksub' 
                btn.append([InlineKeyboardButton("🔄 𝖳𝗋𝗒 𝖠𝗀𝖺𝗂𝗇 🔄", callback_data=f"{pre}#{file_id}")])
            except (IndexError, ValueError):
                btn.append([InlineKeyboardButton("🔄 𝖳𝗋𝗒 𝖠𝗀𝖺𝗂𝗇 🔄", url=f"https://t.me/{temp.U_NAME}?start={message.command[1]}")])
        await client.send_message(
            chat_id=message.from_user.id,
            text="**Please Join My Updates Channel to use this Bot!**",
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=enums.ParseMode.MARKDOWN
            )
        return
        
    if len(message.command) == 2 and message.command[1] in ["subscribe", "error", "okay", "help"]:
        buttons = [[
                    InlineKeyboardButton('◦•●◉✿ ➕ ᴀᴅᴅ ᴍᴇ ᴛᴏ ɢʀᴏᴜᴘ ➕ ✿◉●•◦', url=f"http://t.me/{temp.U_NAME}?startgroup=true")
                ],[
                    InlineKeyboardButton('★⭕ ᴄʜᴀɴɴᴇʟ ⭕★', url="https://t.me/isaimini_updates"),
                    InlineKeyboardButton('★⭕ ᴅᴀɪʟʏ ᴜᴘᴅᴀᴛᴇs ⭕★', url=f"https://t.me/isaimini_daily_update")
                ],[
                    InlineKeyboardButton(']|I{•---» ᴍᴏᴠɪᴇ sᴇᴀʀᴄʜɪɴɢ ɢʀᴏᴜᴘ ʟɪɴᴋs «---•}I|[', url="https://t.me/isaimini_updates/110")
                ],[
                    InlineKeyboardButton('★♻️ ʜᴇʟᴘ ♻️★', callback_data='help'),
                    InlineKeyboardButton('★♻️ ᴀʙᴏᴜᴛ ♻️★', callback_data='about'),
                ],[
                    InlineKeyboardButton('◦•●◉✿ ✅ ᴅᴏɴᴀᴛᴇ ᴍᴇ ✅ ✿◉●•◦', url='https://t.me/isaimini_donation/5')
                  ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            quote=True,
            parse_mode=enums.ParseMode.HTML
        )
        return

    data = message.command[1]
    if data.startswith('verify'):
        _, token = data.split("_", 1)
        verify_status = await get_verify_status(message.from_user.id)
        if verify_status['verify_token'] != token:
            return await message.reply("Your Verification Token is Invalid. Try with Latest Token Link or Contact Admin")
        await update_verify_status(message.from_user.id, is_verified=True, verified_time=time.time())
        if verify_status["link"] == "":
            reply_markup = None
        else:
            btn = [[
                InlineKeyboardButton("◦•●◉✿📁 ʜᴇʀᴇ ɪs ʏᴏᴜʀ ғɪʟᴇ 📁✿◉●•◦", url=f'https://t.me/{temp.U_NAME}?start={verify_status["link"]}')
            ]]
            reply_markup = InlineKeyboardMarkup(btn)
        await message.reply(f"✅ Your token successfully verified and valid for: {next_verify_str}\n<blockquote>Thank You For Using Our Service!\n</blockquote>", reply_markup=reply_markup, quote=True, protect_content=False)
        return
    
    verify_status = await get_verify_status(message.from_user.id)
    user_id = message.from_user.id
    if IS_VERIFY and not verify_status['is_verified'] and user_id not in ADMINS:
        token = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        await update_verify_status(message.from_user.id, verify_token=token, link="" if data == 'inline_verify' else data)
        link = await get_shortlink(SHORTLINK_URL, SHORTLINK_API, f'https://telegram.me/{temp.U_NAME}?start=verify_{token}')
        btn = [[
            InlineKeyboardButton("]|I{•------» 𝙲𝚕𝚒𝚌𝚔 𝚑𝚎𝚛𝚎 «------•}I|[", url=link)
        ],[
            InlineKeyboardButton(']|I{•------» 𝚃𝚞𝚝𝚘𝚛𝚒𝚊𝚕 «------•}I|[', url="https://t.me/how_to_download_isaimini/13")
        ]]
        await message.reply(f"Your Token is expired, Refresh your token and try again.\n\nToken Timeout: {get_readable_time(VERIFY_EXPIRE)}\n<blockquote expandable>What is the token?\n\nToken is the Key to use the bot. If you pass 1 ad, you can use the bot for {get_readable_time(VERIFY_EXPIRE)} with all Benifits. This helps Bot Owner for the Bot Hosting!</blockquote>", reply_markup=InlineKeyboardMarkup(btn), quote=True, protect_content=True)
        return

    if data.split("-", 1)[0] == "SEARCH":
        stick = await message.reply_sticker(sticker="CAACAgUAAx0CZjyOqQACMCpl_EX_Ak6ilEi7sdys1ec9ozSwvQAC3AIAAq9qOVVmHNMuomHDLB4E")
        await asyncio.sleep(1)
        title = data.split("-", 1)[1]
        mov_name = title.replace("_", " ")
        req = message.from_user.id if message.from_user else 0
        key = f"{message.from_user.id}"
        BUTTONS[key] = mov_name
        cap = f"<b>😻<a href=https://graph.org/file/dda3297f0b2396eea3f32.jpg> </a>𝖧𝖾𝗅𝗅𝗈 {message.from_user.mention}\n📂 𝖸𝗈𝗎𝗋 𝖥𝗂𝗅𝖾𝗌 𝖠𝗋𝖾 𝖱𝖾𝖺𝖽𝗒 Below\n<u>𝐁𝐫𝐨𝐮𝐠𝐡𝐭 𝐓𝐨 𝐘𝐨𝐮 𝐁𝐲</u>:- ❤️<a href=https://t.me/isaimini_daily_update>𝗜𝘀𝗮𝗶𝗺𝗶𝗻𝗶 𝗣𝗿𝗶𝗺𝗲</a>❤️\n\n↤↤↤↤↤👇 ʏᴏᴜʀ ғɪʟᴇs 👇↦↦↦↦↦</b>"
        CAP[key] = cap
        pre = 'file'
        files, offset, total_results = await get_search_results(message.chat.id , mov_name.lower(), offset=0, filter=True)
        await asyncio.sleep(1)
        await stick.delete()
        files_link = ""
        if not files:
            return
        btn = []
        end_cap = f"""<b>↤↤↤↤❌ᴇɴᴅ ᴏғ ᴛʜɪs ᴘᴀɢᴇ❌↦↦↦↦</b>"""
        for file in files:
            files_link += f"""\n<blockquote><b>🎬 𝐅𝐢𝐥𝐞: <a href=https://t.me/{temp.U_NAME}?start={pre}_{file.file_id}>{file.file_name}</a></blockquote>\n📁 𝐒𝐢𝐳𝐞: {get_size(file.file_size)}</b>\n"""
            
        btn.insert(0, 
            [
                InlineKeyboardButton(f'📮 Info', 'tips'),
                InlineKeyboardButton(f'🎁 𝖳𝗂𝗉𝗌', 'info')
            ]
            )
        btn.insert(0,
               [InlineKeyboardButton("◦•●◉✿ 📰 𝚂𝚎𝚕𝚎𝚌𝚝 𝙻𝚊𝚗𝚐𝚞𝚊𝚐𝚎 📰 ✿◉●•◦", callback_data=f"languages#{key}#{req}#{offset}")]
              )   
        btn.insert(0, [
            InlineKeyboardButton(f'🎬 {mov_name} 🎬', 'rkbtn')
        ])
        if offset != "":
            try:
                btn.append(
                    [
                InlineKeyboardButton('✅ 🅓🅞🅝🅐🅣🅔 🅤🅢 ✅', url='https://t.me/isaimini_donation/5')
            ])
                btn.append(
                    [InlineKeyboardButton("📃", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="𝖭𝖤𝖷𝖳 ▶️",callback_data=f"next_{req}_{key}_{offset}")]
                )
            except KeyError:
                btn.append(
                    [
                InlineKeyboardButton('✅ 🅓🅞🅝🅐🅣🅔 🅤🅢 ✅', url='https://t.me/isaimini_donation/5')
            ])
                btn.append(
                    [InlineKeyboardButton("📃", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="𝖭𝖤𝖷𝖳 ▶️",callback_data=f"next_{req}_{key}_{offset}")]
                )
        else:
            btn.append(
                [
                InlineKeyboardButton('✅ 🅓🅞🅝🅐🅣🅔 🅤🅢 ✅', url='https://t.me/isaimini_donation/5')
                ])
            btn.append(
                [InlineKeyboardButton(text="❌ 𝖭𝗈 𝖬𝗈𝗋𝖾 𝖯𝖺𝗀𝖾𝗌 𝖠𝗏𝖺𝗂𝗅𝖺𝖻𝗅𝖾 ! ❌",callback_data="pages")]
            )
        fuk = await message.reply_text(text=cap + files_link + end_cap, reply_markup=InlineKeyboardMarkup(btn), protect_content=True, parse_mode=enums.ParseMode.HTML)
        await asyncio.sleep(300)
        await fuk.delete()
        await message.delete()
        return

    try:
        pre, file_id = data.split('_', 1)
    except:
        file_id = data
        pre = ""

    if data.split("-", 1)[0] == "BATCH":
        sts = await message.reply_sticker(sticker="CAACAgUAAx0CZjyOqQACMCpl_EX_Ak6ilEi7sdys1ec9ozSwvQAC3AIAAq9qOVVmHNMuomHDLB4E")
        file_id = data.split("-", 1)[1]
        msgs = BATCH_FILES.get(file_id)
        if not msgs:
            file = await client.download_media(file_id)
            try: 
                with open(file) as file_data:
                    msgs=json.loads(file_data.read())
            except:
                await sts.edit("FAILED")
                return await client.send_message(LOG_CHANNEL, "UNABLE TO OPEN FILE.")
            os.remove(file)
            BATCH_FILES[file_id] = msgs
        await sts.delete()
        for msg in msgs:
            title = msg.get("title")
            size=get_size(int(msg.get("size", 0)))
            f_caption=msg.get("caption", "")
            if BATCH_FILE_CAPTION:
                try:
                    f_caption=BATCH_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                except Exception as e:
                    logger.exception(e)
                    f_caption=f_caption
            if f_caption is None:
                f_caption = f"{title}"
            try:
                await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=msg.get("file_id"),
                    caption=f_caption,
                    protect_content=msg.get('protect', False)                    
                )
            except FloodWait as e:
                await asyncio.sleep(e.x)
                logger.warning(f"Floodwait of {e.x} sec.")
                await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=msg.get("file_id"),
                    caption=f_caption,
                    protect_content=msg.get('protect', False)
                )
            except Exception as e:
                logger.warning(e, exc_info=True)
                continue
            await asyncio.sleep(1) 
        return

    elif data.split("-", 1)[0] == "DSTORE":
        sts = await message.reply_sticker(sticker="CAACAgUAAx0CZjyOqQACMCpl_EX_Ak6ilEi7sdys1ec9ozSwvQAC3AIAAq9qOVVmHNMuomHDLB4E")
        await asyncio.sleep(1)
        b_string = data.split("-", 1)[1]
        decoded = (base64.urlsafe_b64decode(b_string + "=" * (-len(b_string) % 4))).decode("ascii")
        try:
            f_msg_id, l_msg_id, f_chat_id, protect = decoded.split("_", 3)
        except:
            f_msg_id, l_msg_id, f_chat_id = decoded.split("_", 2)
            protect = "/pbatch" if PROTECT_CONTENT else "batch"
        diff = int(l_msg_id) - int(f_msg_id)
        snt_msgs = []
        await sts.delete()
        async for msg in client.iter_messages(int(f_chat_id), int(l_msg_id), int(f_msg_id)):
            if msg.media:
                media = getattr(msg, msg.media.value)
                if BATCH_FILE_CAPTION:
                    try:
                        f_caption=BATCH_FILE_CAPTION.format(file_name=getattr(media, 'file_name', ''), file_size=getattr(media, 'file_size', ''), file_caption=getattr(msg, 'caption', ''))
                    except Exception as e:
                        logger.exception(e)
                        f_caption = getattr(msg, 'caption', '')
                else:
                    media = getattr(msg, msg.media.value)
                    file_name = getattr(media, 'file_name', '')
                    f_caption = getattr(msg, 'caption', file_name)
                try:
                    snt_msg = await msg.copy(message.chat.id, caption=f_caption, protect_content=True if protect == "/pbatch" else False)
                    await asyncio.sleep(0.5)
                    snt_msgs.append(snt_msg)
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    snt_msg = await msg.copy(message.chat.id, caption=f_caption, protect_content=True if protect == "/pbatch" else False)
                    await asyncio.sleep(0.5)
                    snt_msgs.append(snt_msg)
                except Exception as e:
                    logger.exception(e)
                    continue
            elif msg.empty:
                continue
            else:
                try:
                    snt_msg = await msg.copy(message.chat.id, protect_content=True if protect == "/pbatch" else False)
                    await asyncio.sleep(0.5)
                    snt_msgs.append(snt_msg)
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    snt_msg = await msg.copy(message.chat.id, protect_content=True if protect == "/pbatch" else False)
                    await asyncio.sleep(0.5)
                    snt_msgs.append(snt_msg)
                except Exception as e:
                    logger.exception(e)
                    continue
            await asyncio.sleep(1)
        await asyncio.sleep(21600)
        for snt_msg in snt_msgs:
            try:
                await snt_msg.delete()
            except:
                pass
        return
        
    files_ = await get_file_details(file_id)           
    if not files_:
        try:
            pre, file_id = ((base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("utf-8")).split("_", 1)
            msg = await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=file_id,
                protect_content=True,
                reply_markup=InlineKeyboardMarkup( [ [ InlineKeyboardButton('⭕ 𝗝𝗼𝗶𝗻 𝗠𝗮𝗶𝗻 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 ⭕', url=DAILY_UPDATE_LINK) ],[InlineKeyboardButton("✛ ᴡᴀᴛᴄʜ & ᴅᴏᴡɴʟᴏᴀᴅ ✛", callback_data=f"stream#{file_id}")]] ),
            )
            filetype = msg.media
            file = getattr(msg, filetype.value)
            file_cap = file.caption
            size=get_size(file.file_size)
            if(file_cap):
                title = file_cap
            else:
                title = file.file_name
            f_caption = f"<code>{title}</code>"
            if CUSTOM_FILE_CAPTION:
                try:
                    f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='')
                except:
                    return
            await msg.edit_caption(f_caption)
            return
        except:
            pass
        return await message.reply('<b><i>No such file exist.</b></i>')
    files = files_[0]
    files_cap=files.caption
    size=get_size(files.file_size)
    if(files_cap):
        title = files_cap
    else:
        title = files.file_name
    f_caption = f"<code>{title}</code>"
    if CUSTOM_FILE_CAPTION:
        try:
            f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
        except Exception as e:
            logger.exception(e)
            f_caption=f_caption
    if f_caption is None:
        f_caption = f"{files.file_name}"
    await client.send_cached_media(
        chat_id=message.from_user.id,
        file_id=file_id,
        caption=f_caption,
        protect_content=True,
        reply_markup=InlineKeyboardMarkup( [ [ InlineKeyboardButton('⭕ 𝗝𝗼𝗶𝗻 𝗠𝗮𝗶𝗻 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 ⭕', url=DAILY_UPDATE_LINK) ],[InlineKeyboardButton("✛ ᴡᴀᴛᴄʜ & ᴅᴏᴡɴʟᴏᴀᴅ ✛", callback_data=f"stream#{file_id}")]] ),
    )


@Client.on_message(filters.command('telegraph'))
async def telegraph(bot, message):
    reply_to_message = message.reply_to_message
    if not reply_to_message:
        return await message.reply('Reply to any photo or video.')
    file = reply_to_message.photo or reply_to_message.video or None
    if file is None:
        return await message.reply('Invalid media.')
    if file.file_size >= 5242880:
        await message.reply_text(text="Send less than 5MB")   
        return
    text = await message.reply_text(text="ᴘʀᴏᴄᴇssɪɴɢ....")   
    media = await reply_to_message.download()  
    try:
        response = upload_file(media)
    except Exception as e:
        await text.edit_text(text=f"Error - {e}")
        return    
    try:
        os.remove(media)
    except:
        pass
    await text.edit_text(f"<b>❤️ ʏᴏᴜʀ ᴛᴇʟᴇɢʀᴀᴘʜ ʟɪɴᴋ ᴄᴏᴍᴘʟᴇᴛᴇᴅ 👇</b>\n\n<code>https://telegra.ph/{response[0]}</code></b>")

@Client.on_message(filters.command('reset_token') & filters.user(ADMINS))
async def reset_token(bot, message):
    if IS_VERIFY:
        modified_count = await db.reset_all_token()
        return await message.reply_text(f"{modified_count} users tokens reseted!!", quote=True)
    else:
        return await message.reply_text("Token system is disabled!!", quote=True)

@Client.on_message(filters.command('channel') & filters.user(ADMINS))
async def channel_info(bot, message):
           
    """Send basic information of channel"""
    if isinstance(CHANNELS, (int, str)):
        channels = [CHANNELS]
    elif isinstance(CHANNELS, list):
        channels = CHANNELS
    else:
        raise ValueError("Unexpected type of CHANNELS")

    text = '📑 **Indexed channels/groups**\n'
    for channel in channels:
        chat = await bot.get_chat(channel)
        if chat.username:
            text += '\n@' + chat.username
        else:
            text += '\n' + chat.title or chat.first_name

    text += f'\n\n**Total:** {len(CHANNELS)}'

    if len(text) < 4096:
        await message.reply(text)
    else:
        file = 'Indexed channels.txt'
        with open(file, 'w') as f:
            f.write(text)
        await message.reply_document(file)
        os.remove(file)


@Client.on_message(filters.command('logs') & filters.user(ADMINS))
async def log_file(bot, message):
    """Send log file"""
    try:
        await message.reply_document('Logs.txt')
    except Exception as e:
        await message.reply(str(e))

@Client.on_message(filters.command('delete') & filters.user(ADMINS))
async def delete(bot, message):
    """Delete file from database"""
    reply = message.reply_to_message
    if reply and reply.media:
        msg = await message.reply("Processing...⏳", quote=True)
    else:
        await message.reply('Reply to file with /delete which you want to delete', quote=True)
        return

    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, None)
        if media is not None:
            break
    else:
        await msg.edit('This is not supported file format')
        return
    
    file_id, file_ref = unpack_new_file_id(media.file_id)

    result = await Media.collection.delete_one({
        '_id': file_id,
    })
    if result.deleted_count:
        await msg.edit('File is successfully deleted from database')
    else:
        file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
        result = await Media.collection.delete_many({
            'file_name': file_name,
            'file_size': media.file_size,
            'mime_type': media.mime_type
            })
        if result.deleted_count:
            await msg.edit('File is successfully deleted from database')
        else:
            result = await Media.collection.delete_many({
                'file_name': media.file_name,
                'file_size': media.file_size,
                'mime_type': media.mime_type
            })
            if result.deleted_count:
                await msg.edit('File is successfully deleted from database')
            else:
                await msg.edit('File not found in database')


@Client.on_message(filters.command('deleteall') & filters.user(ADMINS))
async def delete_all_index(bot, message):
    await message.reply_text(
        'This will delete all indexed files.\nDo you want to continue??',
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="YES", callback_data="autofilter_delete"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="CANCEL", callback_data="close_data"
                    )
                ],
            ]
        ),
        quote=True,
    )


@Client.on_callback_query(filters.regex(r'^autofilter_delete'))
async def delete_all_index_confirm(bot, message):
    await Media.collection.drop()
    await message.answer('♻️ Please Share and Support ♻️')
    await message.message.edit('Succesfully Deleted All The Indexed Files.')


@Client.on_message(filters.command('settings'))
async def settings(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"You are anonymous admin. Use /connect {message.chat.id} in PM")
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await client.get_chat(grpid)
                title = chat.title
            except:
                await message.reply_text("Make sure I'm present in your group!!", quote=True)
                return
        else:
            await message.reply_text("I'm not connected to any groups!", quote=True)
            return

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        title = message.chat.title

    else:
        return

    st = await client.get_chat_member(grp_id, userid)
    if (
            st.status != enums.ChatMemberStatus.ADMINISTRATOR
            and st.status != enums.ChatMemberStatus.OWNER
            and str(userid) not in ADMINS
    ):
        return
    
    settings = await get_settings(grp_id)

    try:
        if settings['max_btn']:
            settings = await get_settings(grp_id)
    except KeyError:
        await save_group_settings(grp_id, 'max_btn', False)
        settings = await get_settings(grp_id)

    if settings is not None:
        buttons = [
            [
                InlineKeyboardButton(
                    '𝖥𝗂𝗅𝗍𝖾𝗋 𝖡𝗎𝗍𝗍𝗈𝗇',
                    callback_data=f'setgs#button#{settings["button"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '𝖲𝗂𝗇𝗀𝗅𝖾 𝖡𝗎𝗍𝗍𝗈𝗇' if settings["button"] else '𝖣𝗈𝗎𝖻𝗅𝖾',
                    callback_data=f'setgs#button#{settings["button"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    '𝖥𝗂𝗅𝖾 𝖲𝖾𝗇𝖽 𝖬𝗈𝖽𝖾',
                    callback_data=f'setgs#botpm#{settings["botpm"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '𝖬𝖺𝗇𝗎𝖺𝗅 𝖲𝗍𝖺𝗋𝗍' if settings["botpm"] else '𝖠𝗎𝗍𝗈 𝖲𝖾𝗇𝖽',
                    callback_data=f'setgs#botpm#{settings["botpm"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    '𝖯𝗋𝗈𝗍𝖾𝖼𝗍 𝖢𝗈𝗇𝗍𝖾𝗇𝗍',
                    callback_data=f'setgs#file_secure#{settings["file_secure"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✅ 𝖮𝗇' if settings["file_secure"] else '❌ 𝖮𝖿𝖿',
                    callback_data=f'setgs#file_secure#{settings["file_secure"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    '𝖨𝖬𝖣𝖻',
                    callback_data=f'setgs#imdb#{settings["imdb"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✅ 𝖮𝗇' if settings["imdb"] else '❌ 𝖮𝖿𝖿',
                    callback_data=f'setgs#imdb#{settings["imdb"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    '𝖲𝗉𝖾𝗅𝗅 𝖢𝗁𝖾𝖼𝗄',
                    callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✅ 𝖮𝗇' if settings["spell_check"] else '❌ 𝖮𝖿𝖿',
                    callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    '𝖶𝖾𝗅𝖼𝗈𝗆𝖾 𝖬𝖾𝗌𝗌𝖺𝗀𝖾',
                    callback_data=f'setgs#welcome#{settings["welcome"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✅ 𝖮𝗇' if settings["welcome"] else '❌ 𝖮𝖿𝖿',
                    callback_data=f'setgs#welcome#{settings["welcome"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    '𝖠𝗎𝗍𝗈 𝖣𝖾𝗅𝖾𝗍𝖾',
                    callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '5 𝖬𝗂𝗇' if settings["auto_delete"] else '❌ 𝖮𝖿𝖿',
                    callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    '𝖠𝗎𝗍𝗈-𝖥𝗂𝗅𝗍𝖾𝗋',
                    callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✅ 𝖮𝗇' if settings["auto_ffilter"] else '❌ 𝖮𝖿𝖿',
                    callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    '𝖬𝖺𝗑 𝖡𝗎𝗍𝗍𝗈𝗇𝗌',
                    callback_data=f'setgs#max_btn#{settings["max_btn"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '10' if settings["max_btn"] else f'{MAX_B_TN}',
                    callback_data=f'setgs#max_btn#{settings["max_btn"]}#{grp_id}',
                ),
            ],
        ]

        btn = [[
                InlineKeyboardButton("⬇ 𝖮𝗉𝖾𝗇 𝖧𝖾𝗋𝖾 ⬇", callback_data=f"opnsetgrp#{grp_id}"),
                InlineKeyboardButton("➡ 𝖮𝗉𝖾𝗇 𝗂𝗇 𝖯𝖬 ➡", callback_data=f"opnsetpm#{grp_id}")
              ]]

        reply_markup = InlineKeyboardMarkup(buttons)
        if chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            await message.reply_text(
                text="<b>𝖣𝗈 𝖸𝗈𝗎 𝖶𝖺𝗇𝗍 𝖳𝗈 𝖮𝗉𝖾𝗇 𝖲𝖾𝗍𝗍𝗂𝗇𝗀𝗌 𝖧𝖾𝗋𝖾 ?</b>",
                reply_markup=InlineKeyboardMarkup(btn),
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML,
                reply_to_message_id=message.id
            )
        else:
            await message.reply_text(
                text=f"<b>𝖢𝗁𝖺𝗇𝗀𝖾 𝖸𝗈𝗎𝗋 𝖲𝖾𝗍𝗍𝗂𝗇𝗀𝗌 𝖥𝗈𝗋 {title} 𝖠𝗌 𝖸𝗈𝗎𝗋 𝖶𝗂𝗌𝗁</b>",
                reply_markup=reply_markup,
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML,
                reply_to_message_id=message.id
            )

@Client.on_message(filters.command("send") & filters.user(ADMINS))
async def send_msg(bot, message):
    if message.reply_to_message:
        target_id = message.text
        command = ["/send"]
        out = "Users Saved In DB Are:\n\n"
        for cmd in command:
            if cmd in target_id:
                target_id = target_id.replace(cmd, "")
        success = False
        try:
            user = await bot.get_users(target_id)
            users = await db.get_all_users()
            async for usr in users:
                out += f"{usr['id']}"
                out += '\n'
            if str(user.id) in str(out):
                await message.reply_to_message.copy(int(user.id))
                success = True
            else:
                success = False
            if success:
                await message.reply_text(f"<b>Your message has been successfully send to {user.mention}.</b>")
            else:
                await message.reply_text("<b>This user didn't started this bot yet !</b>")
        except Exception as e:
            await message.reply_text(f"<b>Error: {e}</b>")
    else:
        await message.reply_text("<b>Use this command as a reply to any message using the target chat id. For eg: /send userid</b>")

@Client.on_message(filters.command('set_template'))
async def save_template(client, message):
    sts = await message.reply("Checking template")
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"You are anonymous admin. Use /connect {message.chat.id} in PM")
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await client.get_chat(grpid)
                title = chat.title
            except:
                await message.reply_text("Make sure I'm present in your group!!", quote=True)
                return
        else:
            await message.reply_text("I'm not connected to any groups!", quote=True)
            return

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        title = message.chat.title

    else:
        return

    st = await client.get_chat_member(grp_id, userid)
    if (
            st.status != enums.ChatMemberStatus.ADMINISTRATOR
            and st.status != enums.ChatMemberStatus.OWNER
            and str(userid) not in ADMINS
    ):
        return

    if len(message.command) < 2:
        return await sts.edit("No Input!!")
    template = message.text.split(" ", 1)[1]
    await save_group_settings(grp_id, 'template', template)
    await sts.edit(f"Successfully changed template for {title} to\n\n{template}")


@Client.on_message((filters.command(["request", "Request"]) | filters.regex("#request") | filters.regex("#Request")) & filters.group)
async def requests(bot, message):
    if REQST_CHANNEL is None or SUPPORT_CHAT_ID is None: return # Must add REQST_CHANNEL and SUPPORT_CHAT_ID to use this feature
    if message.reply_to_message and SUPPORT_CHAT_ID == message.chat.id:
        chat_id = message.chat.id
        reporter = str(message.from_user.id)
        mention = message.from_user.mention
        success = True
        content = message.reply_to_message.text
        try:
            if REQST_CHANNEL is not None:
                btn = [[
                        InlineKeyboardButton('📥 𝖵𝗂𝖾𝗐 𝖱𝖾𝗊𝗎𝖾𝗌𝗍 📥', url=f"{message.reply_to_message.link}"),
                        InlineKeyboardButton('📝 𝖲𝗁𝗈𝗐 𝖮𝗉𝗍𝗂𝗈𝗇𝗌 📝', callback_data=f'show_option#{reporter}')
                      ]]
                reported_post = await bot.send_message(chat_id=REQST_CHANNEL, text=f"<b>𝖱𝖾𝗉𝗈𝗋𝗍𝖾𝗋 : {mention} ({reporter})\n\n𝖬𝖾𝗌𝗌𝖺𝗀𝖾 : {content}</b>", reply_markup=InlineKeyboardMarkup(btn))
                success = True
            elif len(content) >= 3:
                for admin in ADMINS:
                    btn = [[
                        InlineKeyboardButton('📥 𝖵𝗂𝖾𝗐 𝖱𝖾𝗊𝗎𝖾𝗌𝗍 📥', url=f"{message.reply_to_message.link}"),
                        InlineKeyboardButton('📝 𝖲𝗁𝗈𝗐 𝖮𝗉𝗍𝗂𝗈𝗇𝗌 📝', callback_data=f'show_option#{reporter}')
                      ]]
                    reported_post = await bot.send_message(chat_id=admin, text=f"<b>𝖱𝖾𝗉𝗈𝗋𝗍𝖾𝗋 : {mention} ({reporter})\n\n𝖬𝖾𝗌𝗌𝖺𝗀𝖾 : {content}</b>", reply_markup=InlineKeyboardMarkup(btn))
                    success = True
            else:
                if len(content) < 3:
                    await message.reply_text("<b>You must type about your request [Minimum 3 Characters]. Requests can't be empty.</b>")
            if len(content) < 3:
                success = False
        except Exception as e:
            await message.reply_text(f"Error: {e}")
            pass
        
    elif SUPPORT_CHAT_ID == message.chat.id:
        chat_id = message.chat.id
        reporter = str(message.from_user.id)
        mention = message.from_user.mention
        success = True
        content = message.text
        keywords = ["#request", "/request", "#Request", "/Request"]
        for keyword in keywords:
            if keyword in content:
                content = content.replace(keyword, "")
        try:
            if REQST_CHANNEL is not None and len(content) >= 3:
                btn = [[
                        InlineKeyboardButton('📥 𝖵𝗂𝖾𝗐 𝖱𝖾𝗊𝗎𝖾𝗌𝗍 📥', url=f"{message.link}"),
                        InlineKeyboardButton('📝 𝖲𝗁𝗈𝗐 𝖮𝗉𝗍𝗂𝗈𝗇𝗌 📝', callback_data=f'show_option#{reporter}')
                      ]]
                reported_post = await bot.send_message(chat_id=REQST_CHANNEL, text=f"<b>𝖱𝖾𝗉𝗈𝗋𝗍𝖾𝗋 : {mention} ({reporter})\n\n𝖬𝖾𝗌𝗌𝖺𝗀𝖾 : {content}</b>", reply_markup=InlineKeyboardMarkup(btn))
                success = True
            elif len(content) >= 3:
                for admin in ADMINS:
                    btn = [[
                        InlineKeyboardButton('📥 𝖵𝗂𝖾𝗐 𝖱𝖾𝗊𝗎𝖾𝗌𝗍 📥', url=f"{message.link}"),
                        InlineKeyboardButton('📝 𝖲𝗁𝗈𝗐 𝖮𝗉𝗍𝗂𝗈𝗇𝗌 📝', callback_data=f'show_option#{reporter}')
                      ]]
                    reported_post = await bot.send_message(chat_id=admin, text=f"<b>𝖱𝖾𝗉𝗈𝗋𝗍𝖾𝗋 : {mention} ({reporter})\n\n𝖬𝖾𝗌𝗌𝖺𝗀𝖾 : {content}</b>", reply_markup=InlineKeyboardMarkup(btn))
                    success = True
            else:
                if len(content) < 3:
                    await message.reply_text("<b>You must type about your request [Minimum 3 Characters]. Requests can't be empty.</b>")
            if len(content) < 3:
                success = False
        except Exception as e:
            await message.reply_text(f"Error: {e}")
            pass

    else:
        success = False
    
    if success:
        btn = [[
                InlineKeyboardButton('📥 𝖵𝗂𝖾𝗐 𝖱𝖾𝗊𝗎𝖾𝗌𝗍 📥', url=f"https://t.me/+yAhNuU610EhhMWJh")
              ]]
        await message.reply_text("<b>Your request has been added! Please wait for some time.</b>", reply_markup=InlineKeyboardMarkup(btn))

@Client.on_message(filters.command("usend") & filters.user(ADMINS))
async def send_msg(bot, message):
    if message.reply_to_message:
        target_id = message.text.split(" ", 1)[1]
        out = "Users Saved In DB Are:\n\n"
        success = False
        try:
            user = await bot.get_users(target_id)
            users = await db.get_all_users()
            async for usr in users:
                out += f"{usr['id']}"
                out += '\n'
            if str(user.id) in str(out):
                await message.reply_to_message.copy(int(user.id))
                success = True
            else:
                success = False
            if success:
                await message.reply_text(f"<b>𝖸𝗈𝗎𝗋 𝖬𝖾𝗌𝗌𝖺𝗀𝖾 𝖧𝖺𝗌 𝖲𝗎𝖼𝖼𝖾𝗌𝗌𝖿𝗎𝗅𝗅𝗒 𝖲𝖾𝗇𝗍 𝖳𝗈 {user.mention}.</b>")
            else:
                await message.reply_text("<b>An Error Occured !</b>")
        except Exception as e:
            await message.reply_text(f"<b>Error :- <code>{e}</code></b>")
    else:
        await message.reply_text("<b>Error𝖢𝗈𝗆𝗆𝖺𝗇𝖽 𝖨𝗇𝖼𝗈𝗆𝗉𝗅𝖾𝗍𝖾 !</b>")
        
@Client.on_message(filters.command("send") & filters.user(ADMINS))
async def send_msg(bot, message):
    if message.reply_to_message:
        target_id = message.text.split(" ", 1)[1]
        out = "Users Saved In DB Are:\n\n"
        success = False
        try:
            user = await bot.get_users(target_id)
            users = await db.get_all_users()
            async for usr in users:
                out += f"{usr['id']}"
                out += '\n'
            if str(user.id) in str(out):
                await message.reply_to_message.copy(int(user.id))
                success = True
            else:
                success = False
            if success:
                await message.reply_text(f"<b>Your message has been successfully send to {user.mention}.</b>")
            else:
                await message.reply_text("<b>This user didn't started this bot yet !</b>")
        except Exception as e:
            await message.reply_text(f"<b>Error: {e}</b>")
    else:
        await message.reply_text("<b>Use this command as a reply to any message using the target chat id. For eg: /send userid</b>")

@Client.on_message(filters.command("gsend") & filters.user(ADMINS))
async def send_chatmsg(bot, message):
    if message.reply_to_message:
        target_id = message.text.split(" ", 1)[1]
        out = "Chats Saved In DB Are:\n\n"
        success = False
        try:
            chat = await bot.get_chat(target_id)
            chats = await db.get_all_chats()
            async for cht in chats:
                out += f"{cht['id']}"
                out += '\n'
            if str(chat.id) in str(out):
                await message.reply_to_message.copy(int(chat.id))
                success = True
            else:
                success = False
            if success:
                await message.reply_text(f"<b>Your message has been successfully send to <code>{chat.id}</code>.</b>")
            else:
                await message.reply_text("<b>An Error Occured !</b>")
        except Exception as e:
            await message.reply_text(f"<b>Error :- <code>{e}</code></b>")
    else:
        await message.reply_text("<b>Error𝖢𝗈𝗆𝗆𝖺𝗇𝖽 𝖨𝗇𝖼𝗈𝗆𝗉𝗅𝖾𝗍𝖾 !</b>")

@Client.on_message(filters.command("deletefiles") & filters.user(ADMINS))
async def deletemultiplefiles(bot, message):
    chat_type = message.chat.type
    if chat_type != enums.ChatType.PRIVATE:
        return await message.reply_text(f"<b>Hey {message.from_user.mention}, This command won't work in groups. It only works on my PM !</b>")
    else:
        pass
    try:
        keyword = message.text.split(" ", 1)[1]
    except:
        return await message.reply_text(f"<b>Hey {message.from_user.mention}, Give me a keyword along with the command to delete files.</b>")
    k = await bot.send_message(chat_id=message.chat.id, text=f"<b>Fetching Files for your query {keyword} on DB... Please wait...</b>")
    files, total = await get_bad_files(keyword)
    await k.edit_text(f"<b>Found {total} files for your query {keyword} !\n\nFile deletion process will start in 5 seconds !</b>")
    await asyncio.sleep(5)
    deleted = 0
    for file in files:
        await k.edit_text(f"<b>Process started for deleting files from DB. Successfully deleted {str(deleted)} files from DB for your query {keyword} !\n\nPlease wait...</b>")
        file_ids = file.file_id
        file_name = file.file_name
        result = await Media.collection.delete_one({
            '_id': file_ids,
        })
        if result.deleted_count:
            logger.info(f'File Found for your query {keyword}! Successfully deleted {file_name} from database.')
        deleted += 1
    await k.edit_text(text=f"<b>Process Completed for file deletion !\n\nSuccessfully deleted {str(deleted)} files from database for your query {keyword}.</b>")
