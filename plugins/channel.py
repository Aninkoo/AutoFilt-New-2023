from pyrogram import Client, filters, enums
from info import CHANNELS, INDEX_EXTENSIONS, UPDATES_CHNL
import asyncio
import logging
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import BadRequest
from database.ia_filterdb import save_file
from utils import add_chnl_message, get_poster, temp, getEpisode

media_filter = filters.document | filters.video

@Client.on_message(filters.chat(CHANNELS) & media_filter)
async def media(bot, message):
    """Media Handler"""
    media = getattr(message, message.media.value, None)
    if (str(media.file_name).lower()).endswith(tuple(INDEX_EXTENSIONS)):
        media.caption = message.caption
        text, dup = await save_file(media)
        if dup == 1:
            cap_txt = media.caption if media.caption else media.file_name
            mv_naam, year, languages = await add_chnl_message(cap_txt)
            if mv_naam is not None:
                languages_str = " ".join(languages) if languages else None
                mv_naam = mv_naam.replace(".", " ")
                mv_naamf = media.file_name
                mv_naamf = mv_naamf.replace("."," ")
                mv_naamf = mv_naamf.replace("_"," ")
                season = 100
                if 'S01' in mv_naamf:
                    season = 1
                elif 'S02' in mv_naamf:
                    season = 2
                elif 'S03' in mv_naamf:
                    season = 3
                elif 'S04' in mv_naamf:
                    season = 4
                elif 'S05' in mv_naamf:
                    season = 5
                elif 'S06' in mv_naamf:
                    season = 6
                elif 'S07' in mv_naamf:
                    season = 7
                elif 'S08' in mv_naamf:
                    season = 8
                elif 'S09' in mv_naamf:
                    season = 9
                elif 'S10' in mv_naamf:
                    season = 10
                elif 'S11' in mv_naamf:
                    season = 11
                elif 'S12' in mv_naamf:
                    season = 12
                else:
                    season = 200
                episode = await getEpisode(mv_naamf)
                if year.isdigit() and season == 200:
                    caption = f"<b>#MovieUpdate:\n<blockquote>🧿 <u>𝐍𝐚𝐦𝐞</u> : <code>{mv_naam}</code>\n📆 <u>𝐘𝐞𝐚𝐫</u> : {year}\n"
                else:
                    caption = f"<b>#SeriesUpdate:\n<blockquote>🧿 <u>𝐍𝐚𝐦𝐞</u> : <code>{mv_naam}</code>\n📆 <u>𝐒𝐞𝐚𝐬𝐨𝐧</u> : {season}\n⏳ <u>𝐄𝐩𝐢𝐬𝐨𝐝𝐞</u> : {episode}"
                if languages_str:
                    caption += f"🎙️<u>𝐋𝐚𝐧𝐠𝐮𝐚𝐠𝐞</u> : {languages_str}</blockquote>\n"
                else:
                    caption += f"</blockquote>\n"
                caption += "Click the above name to Copy and Paste In PaxMOVIES' Group to Download👇\n<a href=https://t.me/paxmovies> 𝐏𝐚𝐱𝐌𝐎𝐕𝐈𝐄𝐒' 𝐆𝐫𝐨𝐮𝐩</a></b>"
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
