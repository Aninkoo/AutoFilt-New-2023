import asyncio
import logging
from pyrogram import Client, filters, enums
from pyrogram.errors import BadRequest, FloodWait
from info import CHANNELS, INDEX_EXTENSIONS, UPDATES_CHNL, ASIA_CHNL, ENG_CHNL
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.ia_filterdb import save_file
from utils import add_chnl_message, get_poster, temp, getEpisode, getSeason, mdlsearch
from collections import deque

media_filter = filters.document | filters.video
# Store the last 50 messages
sent_messages = deque(maxlen=50)

@Client.on_message(filters.chat(CHANNELS) & media_filter)
async def media(bot, message):
    media = message.document or message.video
    if not media or not str(media.file_name).lower().endswith(tuple(INDEX_EXTENSIONS)):
        return

    text, dup = await save_file(media)
    if dup != 1:
        logging.info(f"Duplicate file detected: {media.file_name}")
        return

@Client.on_message(filters.chat(ENG_CHNL) & media_filter)
async def eng_media(bot, message):
    global sent_messages  # Ensure we modify the global deque

    media = message.document or message.video
    if not media or not str(media.file_name).lower().endswith(tuple(INDEX_EXTENSIONS)):
        return

    media.caption = message.caption  # Assign caption if it exists
    text, dup = await save_file(media)
    if dup != 1:
        logging.info(f"Duplicate file detected: {media.file_name}")
        return

    cap_txt = media.file_name if media.file_name else media.caption
    mv_naam, year, languages = await add_chnl_message(cap_txt)
    if not mv_naam:
        return

    languages_str = " ".join(languages) if languages else None
    mv_naam = mv_naam.replace(".", " ").replace("_", " ").replace("-", " ")
    mv_naamf = media.file_name.replace(".", " ").replace("_", " ").replace("-", " ")
    search = f"{mv_naam} {year}" if year else mv_naam
    movies = await get_poster(search)
    season = await getSeason(mv_naamf)
    episode = await getEpisode(mv_naamf)

    if season is None:
        season = 1

    caption = f" "
    if year and year.isdigit():
        if episode is None:
            caption = f"<b>#NowAvailable \n#Movie:\n\n<blockquote>🧿 <u>𝐍𝐚𝐦𝐞</u> : <code>{mv_naam}</code>\n\n📆 <u>𝐘𝐞𝐚𝐫</u> : {year}\n\n"
        elif episode == 1:
            caption = f"<b>#NowAvailable \n#Series:\n\n<blockquote>🧿 <u>𝐍𝐚𝐦𝐞</u> : <code>{mv_naam}</code>\n\n📆 <u>𝐘𝐞𝐚𝐫</u> : {year}\n\n🔢 <u>𝐒𝐞𝐚𝐬𝐨𝐧</u> : {season}\n\n⏳ <u>𝐄𝐩𝐢𝐬𝐨𝐝𝐞</u> : {episode}\n\n"
        else:
            caption = f"<b>#SeriesUpdate:\n\n<blockquote>🧿 <u>𝐍𝐚𝐦𝐞</u> : <code>{mv_naam}</code>\n\n📆 <u>𝐘𝐞𝐚𝐫</u> : {year}\n\n🔢 <u>𝐒𝐞𝐚𝐬𝐨𝐧</u> : {season}\n\n⏳ <u>𝐄𝐩𝐢𝐬𝐨𝐝𝐞</u> : {episode}\n\n"
    else:
        if episode is None:
            caption = f"<b>#NowAvailable \n#Movie:\n\n<blockquote>🧿 <u>𝐍𝐚𝐦𝐞</u> : <code>{mv_naam}</code>\n\n"
        elif episode == 1:
            caption = f"<b>#NowAvailable \n#Series:\n\n<blockquote>🧿 <u>𝐍𝐚𝐦𝐞</u> : <code>{mv_naam}</code>\n\n🔢 <u>𝐒𝐞𝐚𝐬𝐨𝐧</u> : {season}\n\n⏳ <u>𝐄𝐩𝐢𝐬𝐨𝐝𝐞</u> : {episode}\n\n"
        else:
            caption = f"<b>#SeriesUpdate:\n\n<blockquote>🧿 <u>𝐍𝐚𝐦𝐞</u> : <code>{mv_naam}</code>\n\n🔢 <u>𝐒𝐞𝐚𝐬𝐨𝐧</u> : {season}\n\n⏳ <u>𝐄𝐩𝐢𝐬𝐨𝐝𝐞</u> : {episode}\n\n"
    if movies and movies.get('genres'):
        caption += f"🎭 <u>𝐆𝐞𝐧𝐫𝐞𝐬</u> : #{movies.get('genres')}\n\n"
    if movies and movies.get('countries'):
        caption += f"🌍 <u>𝐂𝐨𝐮𝐧𝐭𝐫𝐲</u> : #{movies.get('countries')}\n\n"
    if languages_str:
        caption += f"🎙️ <u>𝐋𝐚𝐧𝐠𝐮𝐚𝐠𝐞</u> : #{languages_str}"
    if episode == 1 or episode is None:
        if movies and movie.get('plot'):
            caption += f"📋 <u>𝐏𝐥𝐨𝐭</u> : {movie.get('plot')} </blockquote>\n\n"
    else:
        caption += "</blockquote>\n\n"
    caption += "Click the above name to Copy and Paste In PaxMOVIES' Group to Download👇\n<a href=https://t.me/paxmovies> 𝐏𝐚𝐱𝐌𝐎𝐕𝐈𝐄𝐒' 𝐆𝐫𝐨𝐮𝐩</a></b>"

    search_with_underscore = search.replace(" ", "_")
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('📥 ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ 📥', url=f"http://t.me/{temp.U_NAME}?start=SEARCH-{search_with_underscore}")]])

    # Send message and get the sent message ID
    sent_msg = None
    if movies and movies.get('poster'):
        try:
            sent_msg = await bot.send_photo(
                chat_id=UPDATES_CHNL,
                photo=movies.get('poster'),
                caption=caption,
                reply_markup=markup,
                parse_mode=enums.ParseMode.HTML
            )
        except BadRequest as e:
            sent_msg = await bot.send_message(
                chat_id=UPDATES_CHNL,
                text=caption,
                reply_markup=markup,
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML
            )
    else:
        sent_msg = await bot.send_message(
            chat_id=UPDATES_CHNL,
            text=caption,
            reply_markup=markup,
            disable_web_page_preview=True,
            parse_mode=enums.ParseMode.HTML
        )

    # Store the latest message details in deque
    sent_messages.append({
        "mv_naam": mv_naam,
        "season": season,
        "episode": episode,
        "message_id": sent_msg.id
    })

    # Check if the new message has the same 'mv_naam', 'season', and 'episode' as any previous ones
    # 1. Check if the new message has an earlier episode than any in the list
    for msg in list(sent_messages)[:-1]:  # Exclude the newest message initially
        if msg["mv_naam"] == mv_naam and msg["season"] == season and episode is not None:
            if episode < msg["episode"]:  # New episode is earlier than an existing one
                try:
                    # Delete the new message
                    await bot.delete_messages(chat_id=UPDATES_CHNL, message_ids=sent_messages[-1]["message_id"])
                    logging.info(f"Deleted new message with earlier episode: {mv_naam}, Season {season}, Episode {episode}")
                except Exception as e:
                    logging.error(f"Failed to delete earlier episode message {sent_messages[-1]['message_id']}: {e}")
            
                # Remove only the new message from deque
                sent_messages.pop()
                break  # Exit loop after deleting the new message
            elif episode == msg["episode"]:  # New episode is the same as an existing one
                try:
                    # Delete the new message
                    await bot.delete_messages(chat_id=UPDATES_CHNL, message_ids=sent_messages[-1]["message_id"])
                    logging.info(f"Deleted new message with the same episode: {mv_naam}, Season {season}, Episode {episode}")
                except Exception as e:
                    logging.error(f"Failed to delete same episode message {sent_messages[-1]['message_id']}: {e}")
            
                # Remove only the new message from deque
                sent_messages.pop()
                break  # Exit loop after deleting the new message

    # 2. If none of the above happens, check for previous message with an earlier episode than the new one
    for msg in list(sent_messages)[:-1]:  # Exclude the newest message
        if msg["mv_naam"] == mv_naam and msg["season"] == season and episode is not None:
            if episode > msg["episode"]:  # New episode is later than an existing one
                try:
                    # Delete the previous message with the earlier episode
                    await bot.delete_messages(chat_id=UPDATES_CHNL, message_ids=msg["message_id"])
                    logging.info(f"Deleted previous message with earlier episode: {mv_naam}, Season {season}, Episode {episode}")
                except Exception as e:
                    logging.error(f"Failed to delete earlier episode message {msg['message_id']}: {e}")
            
                # Remove from deque
                sent_messages.remove(msg)
                break  # Exit loop after deleting the previous message

    #await asyncio.sleep(1)

@Client.on_message(filters.chat(ASIA_CHNL) & media_filter)
async def asia_media(bot, message):
    global sent_messages  # Ensure we modify the global deque

    media = message.document or message.video
    if not media or not str(media.file_name).lower().endswith(tuple(INDEX_EXTENSIONS)):
        return

    media.caption = message.caption  # Assign caption if it exists
    text, dup = await save_file(media)
    if dup != 1:
        logging.info(f"Duplicate file detected: {media.file_name}")
        return

    cap_txt = media.file_name if media.file_name else media.caption
    mv_naam, year, languages = await add_chnl_message(cap_txt)
    if not mv_naam:
        return

    languages_str = " ".join(languages) if languages else None
    mv_naam = mv_naam.replace(".", " ").replace("_", " ").replace("-", " ")
    mv_naamf = media.file_name.replace(".", " ").replace("_", " ").replace("-", " ")
    search = f"{mv_naam} {year}" if year else mv_naam
    Title, Rating, Type, Country, Released_date, Episodes, Genre, Synopsis, Poster = await mdlsearch(search)
    season = await getSeason(mv_naamf)
    episode = await getEpisode(mv_naamf)

    if season is None:
        season = 1

    caption = f" "
    if year and year.isdigit():
        if episode is None:
            caption = f"<b>#NowAvailable \n#Movie:\n\n<blockquote>🧿 <u>𝐍𝐚𝐦𝐞</u> : <code>{mv_naam}</code>\n\n📆 <u>𝐘𝐞𝐚𝐫</u> : {year}\n\n"
        elif episode == 1:
            caption = f"<b>#NowAvailable \n#Series:\n\n<blockquote>🧿 <u>𝐍𝐚𝐦𝐞</u> : <code>{mv_naam}</code>\n\n📆 <u>𝐘𝐞𝐚𝐫</u> : {year}\n\n🔢 <u>𝐒𝐞𝐚𝐬𝐨𝐧</u> : {season}\n\n⏳ <u>𝐄𝐩𝐢𝐬𝐨𝐝𝐞</u> : {episode}\n\n"
        else:
            caption = f"<b>#SeriesUpdate:\n\n<blockquote>🧿 <u>𝐍𝐚𝐦𝐞</u> : <code>{mv_naam}</code>\n\n📆 <u>𝐘𝐞𝐚𝐫</u> : {year}\n\n🔢 <u>𝐒𝐞𝐚𝐬𝐨𝐧</u> : {season}\n\n⏳ <u>𝐄𝐩𝐢𝐬𝐨𝐝𝐞</u> : {episode}\n\n"
    else:
        if episode is None:
            caption = f"<b>#NowAvailable \n#Movie:\n\n<blockquote>🧿 <u>𝐍𝐚𝐦𝐞</u> : <code>{mv_naam}</code>\n\n"
        elif episode == 1:
            caption = f"<b>#NowAvailable \n#Series:\n\n<blockquote>🧿 <u>𝐍𝐚𝐦𝐞</u> : <code>{mv_naam}</code>\n\n🔢 <u>𝐒𝐞𝐚𝐬𝐨𝐧</u> : {season}\n\n⏳ <u>𝐄𝐩𝐢𝐬𝐨𝐝𝐞</u> : {episode}\n\n"
        else:
            caption = f"<b>#SeriesUpdate:\n\n<blockquote>🧿 <u>𝐍𝐚𝐦𝐞</u> : <code>{mv_naam}</code>\n\n🔢 <u>𝐒𝐞𝐚𝐬𝐨𝐧</u> : {season}\n\n⏳ <u>𝐄𝐩𝐢𝐬𝐨𝐝𝐞</u> : {episode}\n\n"
    if Genre:
        caption += f"🎭 <u>𝐆𝐞𝐧𝐫𝐞𝐬</u> : #{Genre}\n\n"
    if Country:
        caption += f"🌍 <u>𝐂𝐨𝐮𝐧𝐭𝐫𝐲</u> : #{Country}\n\n"
    if languages_str:
        caption += f"🎙️ <u>𝐋𝐚𝐧𝐠𝐮𝐚𝐠𝐞</u> : #{languages_str}"
    if episode == 1 or episode is None:
        if Synopsis:
            caption += f"📋 <u>𝐒𝐲𝐧𝐨𝐩𝐬𝐢𝐬</u> : {Synopsis} </blockquote>\n\n"
    else:
        caption += "</blockquote>\n\n"
    caption += "Click the above name to Copy and Paste In PaxMOVIES' Group to Download👇\n<a href=https://t.me/paxmovies> 𝐏𝐚𝐱𝐌𝐎𝐕𝐈𝐄𝐒' 𝐆𝐫𝐨𝐮𝐩</a></b>"

    search_with_underscore = search.replace(" ", "_")
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('📥 ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ 📥', url=f"http://t.me/{temp.U_NAME}?start=SEARCH-{search_with_underscore}")]])

    # Send message and get the sent message ID
    sent_msg = None
    if Poster:
        try:
            sent_msg = await bot.send_photo(
                chat_id=UPDATES_CHNL,
                photo=Poster,
                caption=caption,
                reply_markup=markup,
                parse_mode=enums.ParseMode.HTML
            )
        except BadRequest as e:
            sent_msg = await bot.send_message(
                chat_id=UPDATES_CHNL,
                text=caption,
                reply_markup=markup,
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML
            )
    else:
        sent_msg = await bot.send_message(
            chat_id=UPDATES_CHNL,
            text=caption,
            reply_markup=markup,
            disable_web_page_preview=True,
            parse_mode=enums.ParseMode.HTML
        )

    # Store the latest message details in deque
    sent_messages.append({
        "mv_naam": mv_naam,
        "season": season,
        "episode": episode,
        "message_id": sent_msg.id
    })

    # Check if the new message has the same 'mv_naam', 'season', and 'episode' as any previous ones
    # 1. Check if the new message has an earlier episode than any in the list
    for msg in list(sent_messages)[:-1]:  # Exclude the newest message initially
        if msg["mv_naam"] == mv_naam and msg["season"] == season and episode is not None:
            if episode < msg["episode"]:  # New episode is earlier than an existing one
                try:
                    # Delete the new message
                    await bot.delete_messages(chat_id=UPDATES_CHNL, message_ids=sent_messages[-1]["message_id"])
                    logging.info(f"Deleted new message with earlier episode: {mv_naam}, Season {season}, Episode {episode}")
                except Exception as e:
                    logging.error(f"Failed to delete earlier episode message {sent_messages[-1]['message_id']}: {e}")
            
                # Remove only the new message from deque
                sent_messages.pop()
                break  # Exit loop after deleting the new message
            elif episode == msg["episode"]:  # New episode is the same as an existing one
                try:
                    # Delete the new message
                    await bot.delete_messages(chat_id=UPDATES_CHNL, message_ids=sent_messages[-1]["message_id"])
                    logging.info(f"Deleted new message with the same episode: {mv_naam}, Season {season}, Episode {episode}")
                except Exception as e:
                    logging.error(f"Failed to delete same episode message {sent_messages[-1]['message_id']}: {e}")
            
                # Remove only the new message from deque
                sent_messages.pop()
                break  # Exit loop after deleting the new message

    # 2. If none of the above happens, check for previous message with an earlier episode than the new one
    for msg in list(sent_messages)[:-1]:  # Exclude the newest message
        if msg["mv_naam"] == mv_naam and msg["season"] == season and episode is not None:
            if episode > msg["episode"]:  # New episode is later than an existing one
                try:
                    # Delete the previous message with the earlier episode
                    await bot.delete_messages(chat_id=UPDATES_CHNL, message_ids=msg["message_id"])
                    logging.info(f"Deleted previous message with earlier episode: {mv_naam}, Season {season}, Episode {episode}")
                except Exception as e:
                    logging.error(f"Failed to delete earlier episode message {msg['message_id']}: {e}")
            
                # Remove from deque
                sent_messages.remove(msg)
                break  # Exit loop after deleting the previous message

