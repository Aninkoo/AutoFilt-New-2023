from pyrogram import Client, filters, enums
from info import CHANNELS, INDEX_EXTENSIONS, UPDATES_CHNL
import asyncio
import logging
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import BadRequest
from database.ia_filterdb import save_file
from utils import add_chnl_message, get_poster, temp, getEpisode, getSeason

# Define the media filter for document and video
media_filter = filters.document | filters.video

@Client.on_message(filters.chat(CHANNELS) & media_filter)
async def media(bot, message):
    """Media Handler"""
    # Get the media file from the message
    media = None
    if message.document:
        media = message.document
    elif message.video:
        media = message.video

    # If no media found, return
    if not media:
        return

    # Check if the file extension matches the desired index extensions
    if str(media.file_name).lower().endswith(tuple(INDEX_EXTENSIONS)):
        media.caption = message.caption  # Assign caption if it exists

        # Attempt to save the file
        text, dup = await save_file(media)

        if dup == 1:
            # If the file is not a duplicate, process the message
            cap_txt = media.caption if media.caption else media.file_name
            mv_naam, year, languages = await add_chnl_message(cap_txt)

            if mv_naam:
                # Process the movie name and year
                languages_str = " ".join(languages) if languages else None
                mv_naam = mv_naam.replace(".", " ").replace("_", " ")
                mv_naamf = media.file_name.replace(".", " ").replace("_", " ")

                # Get season and episode details
                season = await getSeason(mv_naamf)
                episode = await getEpisode(mv_naamf)

                if season is None and episode is not None:
                    season = 1  # Default season if episode is found but no season

                # Create the caption for the post
                if year.isdigit() and episode is None:
                    caption = f"<b>#MovieUpdate:\n\n<blockquote>🧿 <u>𝐍𝐚𝐦𝐞</u> : <code>{mv_naam}</code>\n\n📆 <u>𝐘𝐞𝐚𝐫</u> : {year}\n\n"
                elif year.isdigit() and episode is not None:
                    caption = f"<b>#SeriesUpdate:\n\n<blockquote>🧿 <u>𝐍𝐚𝐦𝐞</u> : <code>{mv_naam}</code>\n\n📆 <u>𝐘𝐞𝐚𝐫</u> : {year}\n\n🔢 <u>𝐒𝐞𝐚𝐬𝐨𝐧</u> : {season}\n\n⏳ <u>𝐄𝐩𝐢𝐬𝐨𝐝𝐞</u> : {episode}\n\n"
                else:
                    caption = f"<b>#SeriesUpdate:\n\n<blockquote>🧿 <u>𝐍𝐚𝐦𝐞</u> : <code>{mv_naam}</code>\n\n🔢 <u>𝐒𝐞𝐚𝐬𝐨𝐧</u> : {season}\n\n⏳ <u>𝐄𝐩𝐢𝐬𝐨𝐝𝐞</u> : {episode}\n\n"

                # Add language information to caption if available
                if languages_str:
                    caption += f"🎙️<u>𝐋𝐚𝐧𝐠𝐮𝐚𝐠𝐞</u> : {languages_str}</blockquote>\n\n"
                else:
                    caption += "</blockquote>\n"

                # Add the download link
                caption += "Click the above name to Copy and Paste In PaxMOVIES' Group to Download👇\n<a href=https://t.me/paxmovies> 𝐏𝐚𝐱𝐌𝐎𝐕𝐈𝐄𝐒' 𝐆𝐫𝐨𝐮𝐩</a></b>"

                # Search for the movie poster
                search = f"{mv_naam} {year}" if year else mv_naam
                movies = await get_poster(search)
                search_with_underscore = search.replace(" ", "_")

                # Create the button with the search link
                btn = [[
                    InlineKeyboardButton('📥 ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ 📥', url=f"http://t.me/{temp.U_NAME}?start=SEARCH-{search_with_underscore}")
                ]]
                markup = InlineKeyboardMarkup(btn)

                # Try to send the movie poster or fallback to sending just the caption
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
                        logging.error(f"Error sending photo: {e}")
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

                # Pause between updates to avoid flooding the channel
                # await asyncio.sleep(2)

        else:
            logging.info(f"Duplicate file detected: {media.file_name}")
    else:
        logging.info(f"File {media.file_name} does not match the required extensions.")
