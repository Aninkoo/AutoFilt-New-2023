from pyrogram import Client, filters, enums
from info import CHANNELS, INDEX_EXTENSIONS, UPDATES_CHNL
import asyncio
import logging
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import BadRequest
from database.ia_filterdb import save_file
from utils import add_chnl_message, get_poster, temp

media_filter = filters.document | filters.video

@Client.on_message(filters.chat(CHANNELS) & media_filter)
async def media(bot, message):
    """Media Handler"""
    media = getattr(message, message.media.value, None)
    if (str(media.file_name).lower()).endswith(tuple(INDEX_EXTENSIONS)):
        media.caption = message.caption
        text, dup = await save_file(media)
        if dup == 1:
            cap_txt = media.file_name
            mv_naam, year, languages = await add_chnl_message(cap_txt)
            if mv_naam is not None:
                languages_str = " ".join(languages) if languages else None
                mv_naam = mv_naam.replace(".", " ")
                season = 10
                if 'S02' in mv_naam:
                    season = 2
                elif 'S03' in mv_naam:
                    season = 3
                else:
                    season = 1
                if year.isdigit():
                    caption = f"<b>#MovieUpdate:\n<blockquote>🧿 <u>𝐍𝐚𝐦𝐞</u> : <code>{mv_naam}</code>\n📆 <u>𝐘𝐞𝐚𝐫</u> : {year}\n"
                else:
                    caption = f"<b>#SeriesUpdate:\n<blockquote>🧿 <u>𝐍𝐚𝐦𝐞</u> : <code>{mv_naam}</code>\n📆 <u>𝐒𝐞𝐚𝐬𝐨𝐧</u> : {season}"
                if languages_str:
                    caption += f"🎙️<u>𝐋𝐚𝐧𝐠𝐮𝐚𝐠𝐞</u> : {languages_str}</blockquote>\n"
                else:
                    caption += f"</blockquote>\n"
                caption += "Copy only Movie Name & Paste In👇\n---»<a href=https://t.me/paxmovies> ᴍᴏᴠɪᴇ sᴇᴀʀᴄʜɪɴɢ ɢʀᴏᴜᴘ ʟɪɴᴋs </a>«---</b>"
                search = f"{mv_naam} {year}" if year is not None else mv_naam
                movies = await get_poster(search)
                search_with_underscore = search.replace(" ", "_")
                btn = [[
                    InlineKeyboardButton('📥 ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ 📥', url=f"http://t.me/{temp.U_NAME}?start=SEARCH-{search_with_underscore}")
                ]]
                markup = InlineKeyboardMarkup(btn)
                if movies and movies.get('poster'):
                    try:
                        await bot.send_photo(
                            chat_id=UPDATES_CHNL,
                            photo=movies.get('poster'),
                            caption=caption,
                            reply_markup=markup,
                            parse_mode=enums.ParseMode.HTML
                        )
                    except BadRequest as e:
                        await bot.send_message(
                            chat_id=UPDATES_CHNL,
                            text=caption,
                            reply_markup=markup,
                            disable_web_page_preview=True,
                            parse_mode=enums.ParseMode.HTML
                        )
                else:
                    await bot.send_message(
                        chat_id=UPDATES_CHNL,
                        text=caption,
                        reply_markup=markup,
                        disable_web_page_preview=True,
                        parse_mode=enums.ParseMode.HTML
                    )
                logger.info(f'{mv_naam} {year} - Update Sent to Channel!')
                await asyncio.sleep(5)
        else:
            return
