import asyncio
import logging
from pyrogram import Client, filters, enums
from pyrogram.errors import BadRequest, FloodWait
from info import CHANNELS, INDEX_EXTENSIONS, UPDATES_CHNL
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.ia_filterdb import save_file
from utils import add_chnl_message, get_poster, temp, getEpisode, getSeason

media_filter = filters.document | filters.video

@Client.on_message(filters.chat(CHANNELS) & media_filter)
async def media(bot, message):
    media = message.document or message.video
    if not media or not str(media.file_name).lower().endswith(tuple(INDEX_EXTENSIONS)):
        return

    media.caption = message.caption  # Assign caption if it exists
    text, dup = await save_file(media)
    if dup != 1:
        logging.info(f"Duplicate file detected: {media.file_name}")
        #return

    cap_txt = media.file_name if media.file_name else media.caption
    mv_naam, year, languages = await add_chnl_message(cap_txt)
    if not mv_naam:
        return

    languages_str = " ".join(languages) if languages else None
    mv_naam = mv_naam.replace(".", " ").replace("_", " ").replace("-", " ")
    mv_naamf = media.file_name.replace(".", " ").replace("_", " ").replace("-", " ")
    season = await getSeason(mv_naamf) or (1 if await getSeason(mv_naamf) is None)
    episode = await getEpisode(mv_naamf)

    caption = f" "
    if year and year.isdigit():
        if episode is None:
            caption = f"<b>#MovieUpdate:\n\n<blockquote>🧿 <u>𝐍𝐚𝐦𝐞</u> : <code>{mv_naam}</code>\n\n📆 <u>𝐘𝐞𝐚𝐫</u> : {year}\n\n"
        else:
            caption = f"<b>#SeriesUpdate:\n\n<blockquote>🧿 <u>𝐍𝐚𝐦𝐞</u> : <code>{mv_naam}</code>\n\n📆 <u>𝐘𝐞𝐚𝐫</u> : {year}\n\n🔢 <u>𝐒𝐞𝐚𝐬𝐨𝐧</u> : {season}\n\n⏳ <u>𝐄𝐩𝐢𝐬𝐨𝐝𝐞</u> : {episode}\n\n"
    else:
        if episode is None:
            caption = f"<b>#MovieUpdate:\n\n<blockquote>🧿 <u>𝐍𝐚𝐦𝐞</u> : <code>{mv_naam}</code>\n\n"
        else:
            caption = f"<b>#SeriesUpdate:\n\n<blockquote>🧿 <u>𝐍𝐚𝐦𝐞</u> : <code>{mv_naam}</code>\n\n🔢 <u>𝐒𝐞𝐚𝐬𝐨𝐧</u> : {season}\n\n⏳ <u>𝐄𝐩𝐢𝐬𝐨𝐝𝐞</u> : {episode}\n\n"
    if languages_str:
        caption += f"🎙️<u>𝐋𝐚𝐧𝐠𝐮𝐚𝐠𝐞</u> : {languages_str}</blockquote>\n\n"
    else:
        caption += "</blockquote>\n\n"
    caption += "Click the above name to Copy and Paste In PaxMOVIES' Group to Download👇\n<a href=https://t.me/paxmovies> 𝐏𝐚𝐱𝐌𝐎𝐕𝐈𝐄𝐒' 𝐆𝐫𝐨𝐮𝐩</a></b>"

    search = f"{mv_naam} {year}" if year else mv_naam
    movies = await get_poster(search)
    search_with_underscore = search.replace(" ", "_")
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('📥 ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ 📥', url=f"http://t.me/{temp.U_NAME}?start=SEARCH-{search_with_underscore}")]])

    async def send_message():
        while True:
            try:
                if movies and movies.get('poster'):
                    await bot.send_photo(UPDATES_CHNL, movies['poster'], caption=caption, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
                else:
                    await bot.send_message(UPDATES_CHNL, caption, reply_markup=markup, disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML)
                break  # Exit loop on success
            except FloodWait as e:
                logging.warning(f"Flood wait triggered. Sleeping for {e.value} seconds.")
                await asyncio.sleep(e.value)  # Wait for the required time
            except BadRequest as e:
                logging.error(f"BadRequest error: {e}")
                break  # Stop retrying if it's a bad request error
            except Exception as e:
                logging.error(f"Error sending message: {e}")
                await asyncio.sleep(5)  # Retry after 5 seconds

    await send_message()
    
