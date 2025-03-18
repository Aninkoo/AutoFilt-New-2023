import aiohttp
import json
import logging
from pyrogram.errors import InputUserDeactivated, UserNotParticipant, FloodWait, UserIsBlocked, PeerIdInvalid
from info import AUTH_CHANNEL, LONG_IMDB_DESCRIPTION, MAX_LIST_ELM, CUSTOM_FILE_CAPTION, UPDATES_CHNL, SHORTLINK_URL
from imdb import Cinemagoer 
import asyncio
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import enums
from random import choice 
import re
import os
import time
import pytz
from datetime import datetime
from typing import List, Any, Union, Optional, AsyncGenerator
from database.users_chats_db import db
from bs4 import BeautifulSoup
import requests
from fuzzywuzzy import fuzz  # For fuzzy string matching
from shortzy import Shortzy
import httpx
from httpx import AsyncClient, Timeout

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

TOT_SHORT = len(SHORTLINK_URL)
tot_short = TOT_SHORT - 1

BTN_URL_REGEX = re.compile(
    r"(([^]+?)(buttonurl|buttonalert):(?:/{0,2})(.+?)(:same)?)"
)

imdb = Cinemagoer() 

BANNED = {}
SMART_OPEN = '“'
SMART_CLOSE = '”'
START_CHAR = ('\'', '"', SMART_OPEN)
update_list = set()

# HTTPx Async Client
fetch = AsyncClient(
    verify=False,
    headers={
        "Accept-Language": "en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edge/107.0.1418.42",
    },
    timeout=Timeout(20),
)

# Temporary database for banned users and other settings
class Temp:
    BANNED_USERS = []
    BANNED_CHATS = []
    ME = None
    CURRENT = int(os.environ.get("SKIP", 2))
    CANCEL = False
    MELCOW = {}
    FILES = {}
    U_NAME = None
    B_NAME = None
    SETTINGS = {}
    FILES_IDS = {}
    SPELL_CHECK = {}
    BOT = None

async def fetch_with_retries(url, max_retries=60):
    retries = 0
    while retries < max_retries:
        try:
            response = await fetch.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx, 5xx)
            return response.json()  # ✅ FIX: No need to await
        except Exception as e:
            retries += 1
            logger.warning(f"Attempt {retries} failed: {e}")
            if retries >= max_retries:
                raise  # Re-raise the exception if max retries reached
            await asyncio.sleep(1)
    return None  # Return None if all retries fail

async def is_subscribed(bot, query):
    try:
        user = await bot.get_chat_member(AUTH_CHANNEL, query.from_user.id)
    except UserNotParticipant:
        return False
    except Exception as e:
        logger.exception(e)
        return False
    return user.status != enums.ChatMemberStatus.BANNED

async def getEpisode(filename):
    match = re.search(r'(?ix)(?:E(\d{1,2})|S\d{1,2}E(\d{1,2})|Ep(\d{1,2})|episode (\d+))', filename)
    if match:
        return match.group(1) or match.group(2) or match.group(3) or match.group(4)
    return None

async def getSeason(filename):
    match = re.search(r'(?ix)(?:season (\d{1,2})|S(\d{1,2}))', filename)
    if match:
        return match.group(1) or match.group(2)
    return None

async def get_poster(query, bulk=False, id=False, file=None):
    if not id and query is not None:
        query = query.strip().lower()
        title = query
        year = re.findall(r'[1-2]\d{3}$', query, re.IGNORECASE)
        if year:
            year = year[0]
            title = query.replace(year, "").strip()
        elif file is not None:
            year = re.findall(r'[1-2]\d{3}', file, re.IGNORECASE)
            if year:
                year = year[0]
        else:
            year = None

        movie_list = imdb.search_movie(title, results=10)
        if not movie_list:
            return None

        filtered = [m for m in movie_list if str(m.get('year')) == str(year)] if year else movie_list
        movie_list = [m for m in filtered if m.get('kind') in ['movie', 'tv series']] or filtered

        if not movie_list:
            return None
        movie_id = movie_list[0].movieID
    else:
        movie_id = query

    movie = imdb.get_movie(movie_id)
    date = movie.get("original air date") or movie.get("year") or "N/A"
    plot = movie.get('plot outline') if LONG_IMDB_DESCRIPTION else (movie.get('plot') or [""])[0]
    if plot and len(plot) > 800:
        plot = plot[:800] + "..."

    return {
        'title': movie.get('title'),
        'votes': movie.get('votes'),
        "aka": list_to_str(movie.get("akas")),
        "seasons": movie.get("number of seasons"),
        "box_office": movie.get('box office'),
        'localized_title': movie.get('localized title'),
        'kind': movie.get("kind"),
        "imdb_id": f"tt{movie.get('imdbID')}",
        "cast": list_to_str(movie.get("cast")),
        "runtime": list_to_str(movie.get("runtimes")),
        "countries": list_to_str(movie.get("countries")),
        "certificates": list_to_str(movie.get("certificates")),
        "languages": list_to_str(movie.get("languages")),
        "director": list_to_str(movie.get("director")),
        "writer": list_to_str(movie.get("writer")),
        "producer": list_to_str(movie.get("producer")),
        "composer": list_to_str(movie.get("composer")),
        "cinematographer": list_to_str(movie.get("cinematographer")),
        "music_team": list_to_str(movie.get("music department")),
        "distributors": list_to_str(movie.get("distributors")),
        'release_date': date,
        'year': movie.get('year'),
        'genres': list_to_str(movie.get("genres")),
        'poster': movie.get('full-size cover url'),
        'plot': plot,
        'plots': movie.get('plot'),
        'rating': str(movie.get("rating")),
        'url': f'https://www.imdb.com/title/tt{movie_id}'
}

async def filter_dramas(query: str, max_retries: int = 60) -> str:
    """
    Searches for dramas using an external API.
    Retries up to `max_retries` times if no result is found.
    Returns the 'slug' of the best matching drama, excluding those with a year greater than the current year.
    """
    retries = 0
    current_year = datetime.now().year  # Get the current year

    async with httpx.AsyncClient() as client:
        while retries < max_retries:
            try:
                response = await client.get(
                    f"https://kuryana.vercel.app/search/q/{query}",
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                if response.status_code == 200:
                    data = response.json()
                    dramas = data.get("results", {}).get("dramas", [])
                    if dramas:
                        best_match = max(
                            (d for d in dramas if int(d.get("year", 0)) <= current_year),
                            key=lambda d: fuzz.ratio(query.lower(), d.get("title", "").lower()),
                            default=None,
                        )
                        return best_match.get("slug", "") if best_match else ""
                retries += 1
                logger.warning(f"Retry {retries}: No results found. Retrying...")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"An error occurred: {e}")
                retries += 1
                await asyncio.sleep(1)

    logger.warning(f"Max retries ({max_retries}) reached. Returning empty string.")
    return ""

async def broadcast_messages(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        await message.pin()
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await broadcast_messages(user_id, message)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        logger.info(f"{user_id} - Removed from Database (deleted account).")
        return False, "Deleted"
    except UserIsBlocked:
        logger.info(f"{user_id} - Blocked the bot.")
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        logger.info(f"{user_id} - PeerIdInvalid.")
        return False, "Error"
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False, "Error"

async def broadcast_messages_group(chat_id, message):
    try:
        msg = await message.copy(chat_id=chat_id)
        try:
            await msg.pin()
        except Exception:
            pass
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await broadcast_messages_group(chat_id, message)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False, "Error"

async def search_gagala(text):
    """Performs a Google search and returns a list of result titles."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/61.0.3163.100 Safari/537.36'
    }
    text = text.replace(" ", "+")
    url = f'https://www.google.com/search?q={text}'

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    titles = soup.find_all('h3')
    return [title.getText() for title in titles]

async def get_settings(group_id):
    """Fetches group settings from cache or database."""
    settings = Temp.SETTINGS.get(group_id)
    if not settings:
        settings = await db.get_settings(group_id)
        Temp.SETTINGS[group_id] = settings
    return settings

async def save_group_settings(group_id, key, value):
    """Saves updated group settings to cache and database."""
    current = await get_settings(group_id)
    current[key] = value
    Temp.SETTINGS[group_id] = current
    await db.update_settings(group_id, current)

def get_size(size):
    """Converts file size into human-readable format."""
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units) - 1:
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

def split_list(lst, n):
    """Splits a list into smaller lists of size n."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def get_file_id(msg: Message):
    """Extracts the file ID from a media message."""
    if msg.media:
        for message_type in (
            "photo", "animation", "audio", "document", "video",
            "video_note", "voice", "sticker"
        ):
            obj = getattr(msg, message_type, None)
            if obj:
                setattr(obj, "message_type", message_type)
                return obj
    return None

def extract_user(message: Message) -> Union[int, str]:
    """Extracts user ID and first name from a message."""
    user_id = None
    user_first_name = None

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        user_first_name = message.reply_to_message.from_user.first_name
    elif len(message.command) > 1:
        if (
            len(message.entities) > 1 and
            message.entities[1].type == enums.MessageEntityType.TEXT_MENTION
        ):
            required_entity = message.entities[1]
            user_id = required_entity.user.id
            user_first_name = required_entity.user.first_name
        else:
            user_id = message.command[1]
            user_first_name = user_id
        try:
            user_id = int(user_id)
        except ValueError:
            pass
    else:
        user_id = message.from_user.id
        user_first_name = message.from_user.first_name

    return user_id, user_first_name

def list_to_str(k):
    """Converts a list to a string with elements separated by commas."""
    if not k:
        return "N/A"
    elif len(k) == 1:
        return str(k[0])
    elif MAX_LIST_ELM:
        k = k[:int(MAX_LIST_ELM)]
        return ', '.join(k)
    else:
        return ', '.join(k)

def last_online(from_user):
    """Returns a formatted string representing the last online status of a user."""
    if from_user.is_bot:
        return "🤖 Bot :("
    elif from_user.status == enums.UserStatus.RECENTLY:
        return "Recently"
    elif from_user.status == enums.UserStatus.LAST_WEEK:
        return "Within the last week"
    elif from_user.status == enums.UserStatus.LAST_MONTH:
        return "Within the last month"
    elif from_user.status == enums.UserStatus.LONG_AGO:
        return "A long time ago :("
    elif from_user.status == enums.UserStatus.ONLINE:
        return "Currently Online"
    elif from_user.status == enums.UserStatus.OFFLINE:
        return from_user.last_online_date.strftime("%a, %d %b %Y, %H:%M:%S")
    return "Unknown"

def split_quotes(text: str) -> List[str]:
    """Splits a string based on quotation marks."""
    if not any(text.startswith(char) for char in START_CHAR):
        return text.split(None, 1)

    counter = 1
    while counter < len(text):
        if text[counter] == "\\":
            counter += 1
        elif text[counter] == text[0] or (text[0] == SMART_OPEN and text[counter] == SMART_CLOSE):
            break
        counter += 1
    else:
        return text.split(None, 1)

    key = remove_escapes(text[1:counter].strip())
    rest = text[counter + 1:].strip()
    return list(filter(None, [key, rest]))

def gfilterparser(text, keyword):
    """Parses text to extract buttons and alerts for inline keyboard formatting."""
    if "buttonalert" in text:
        text = text.replace("\n", "\\n").replace("\t", "\\t")

    buttons = []
    note_data = ""
    prev = 0
    i = 0
    alerts = []

    for match in BTN_URL_REGEX.finditer(text):
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and text[to_check] == "\\":
            n_escapes += 1
            to_check -= 1

        if n_escapes % 2 == 0:
            note_data += text[prev:match.start(1)]
            prev = match.end(1)

            if match.group(3) == "buttonalert":
                if bool(match.group(5)) and buttons:
                    buttons[-1].append(InlineKeyboardButton(
                        text=match.group(2),
                        callback_data=f"gfilteralert:{i}:{keyword}"
                    ))
                else:
                    buttons.append([InlineKeyboardButton(
                        text=match.group(2),
                        callback_data=f"gfilteralert:{i}:{keyword}"
                    )])
                i += 1
                alerts.append(match.group(4))
            elif bool(match.group(5)) and buttons:
                buttons[-1].append(InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(4).replace(" ", "")
                ))
            else:
                buttons.append([InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(4).replace(" ", "")
                )])
        else:
            note_data += text[prev:to_check]
            prev = match.start(1) - 1
    else:
        note_data += text[prev:]

    return note_data, buttons, alerts if alerts else None

def parser(text, keyword):
    """Similar to gfilterparser but used for normal parsing."""
    if "buttonalert" in text:
        text = text.replace("\n", "\\n").replace("\t", "\\t")

    buttons = []
    note_data = ""
    prev = 0
    i = 0
    alerts = []

    for match in BTN_URL_REGEX.finditer(text):
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and text[to_check] == "\\":
            n_escapes += 1
            to_check -= 1

        if n_escapes % 2 == 0:
            note_data += text[prev:match.start(1)]
            prev = match.end(1)

            if match.group(3) == "buttonalert":
                if bool(match.group(5)) and buttons:
                    buttons[-1].append(InlineKeyboardButton(
                        text=match.group(2),
                        callback_data=f"alertmessage:{i}:{keyword}"
                    ))
                else:
                    buttons.append([InlineKeyboardButton(
                        text=match.group(2),
                        callback_data=f"alertmessage:{i}:{keyword}"
                    )])
                i += 1
                alerts.append(match.group(4))
            elif bool(match.group(5)) and buttons:
                buttons[-1].append(InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(4).replace(" ", "")
                ))
            else:
                buttons.append([InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(4).replace(" ", "")
                )])
        else:
            note_data += text[prev:to_check]
            prev = match.start(1) - 1
    else:
        note_data += text[prev:]

    return note_data, buttons, alerts if alerts else None

def remove_escapes(text: str) -> str:
    """Removes escape characters from text."""
    res = ""
    is_escaped = False
    for char in text:
        if is_escaped:
            res += char
            is_escaped = False
        elif char == "\\":
            is_escaped = True
        else:
            res += char
    return res

async def send_react(chat_info, message):
    """Sends a random reaction emoji in a chat."""
    available_reactions = chat_info.available_reactions
    full_emoji_set = {
        "🙏", "🤗", "👾", "🤝", "🎉", "🌚", "👨‍💻", "😎", "😇",
        "🕊", "💘", "🔥", "🥰", "🗿", "❤️‍🔥", "🍾", "🎃",
        "👻", "🏆", "☃️", "💯", "⚡", "🙈", "😘", "🤩", "😍"
    }
    if available_reactions:
        if getattr(available_reactions, "all_are_enabled", False):
            emojis = full_emoji_set
        else:
            emojis = {reaction.emoji for reaction in available_reactions.reactions}
        await message.react(choice(list(emojis)), big=True)

async def get_verify_status(user_id):
    """Fetches verification status for a user."""
    return await db.get_verify_status(user_id)

async def update_verify_status(user_id, verify_token="", is_verified=False, verified_time=0, link="", no_short=None):
    """Updates verification status for a user."""
    current = await get_verify_status(user_id)
    current['verify_token'] = verify_token
    current['is_verified'] = is_verified
    current['verified_time'] = verified_time
    current['link'] = link
    if no_short is not None:
        current['no_short'] = min(no_short, tot_short)
    await db.update_verify_status(user_id, current)

async def get_shortlink(url, api, link):
    """Generates a short link using the Shortzy API."""
    shortzy = Shortzy(api_key=api, base_site=url)
    return await shortzy.convert(link)

def get_readable_time(seconds):
    """Converts seconds into a human-readable time format."""
    periods = [('day', 86400), ('hours', 3600), ('mins', 60), ('secs', 1)]
    result = ''
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result += f'{int(period_value)}{period_name} '
    return result.strip()

async def add_chnl_message(file_name):
    """Extracts movie name, year, and language from the file name."""
    patterns = [
        r'^([\w\s-]+)\s(S\d{2})\s?(E(P|p)|E)\d{2}\s',
        r'^([\w\.-]+)\.(S\d{2})(E(P|p)|E|e)\d{2}\.',
        r'^([\w\s]+)\s(\d{4})\s(.*?)\s',
        r'^([\w\.]+)\.(\d{4})\.(.*?)\.'
    ]

    for pat in patterns:
        match = re.match(pat, file_name)
        if match:
            movie_name = match.group(1)
            year = match.group(2) if len(match.groups()) > 1 else None
            mov_name = file_name.lower()
            detected_languages = []
            language_keywords = ["tamil", "telugu", "malayalam", "kannada", "english", "hindi", "korean", "japanese"]
            episode = await getEpisode(file_name)

            if episode:
                return movie_name, year, None

            for lang in language_keywords:
                if lang in mov_name:
                    detected_languages.append(lang.capitalize())

            if detected_languages:
                key = (movie_name, detected_languages[0])
            else:
                key = (movie_name, "No Lang")

            if key in update_list:
                return None, None, None

            update_list.add(key)
            return movie_name, year, detected_languages if detected_languages else None

    return None, None, None

def humanbytes(size):
    """Converts file size into a human-readable format."""
    if not size:
        return ""
    power = 2**10
    n = 0
    unit_dict = {0: '', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size >= power and n < len(unit_dict) - 1:
        size /= power
        n += 1
    return f"{round(size, 2)} {unit_dict[n]}B"

async def send_all(bot, userid, files, ident):
    """Sends cached media files to a user with a custom caption."""
    for file in files:
        f_caption = file.caption
        title = file.file_name
        size = get_size(file.file_size)

        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(
                    file_name=title or "",
                    file_size=size or "",
                    file_caption=f_caption or ""
                )
            except Exception as e:
                logger.error(f"Error formatting caption: {e}")
                f_caption = f_caption or title

        await bot.send_cached_media(
            chat_id=userid,
            file_id=file.file_id,
            caption=f_caption or title,
            protect_content=True if ident == "filep" else False,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('⚔️ 𝖯𝖨𝖱𝖮 𝖴𝖯𝖣𝖠𝖳𝖤𝖲 ⚔️', url="https://t.me/piroxbots")]
            ])
    )

async def get_movie_details(title: str):
    """Fetches movie details from IMDb based on the given title."""
    search_results = imdb.search_movie(title, results=5)
    if not search_results:
        return None

    movie_id = search_results[0].movieID
    movie = imdb.get_movie(movie_id)

    details = {
        "title": movie.get("title"),
        "year": movie.get("year"),
        "rating": movie.get("rating"),
        "genres": list_to_str(movie.get("genres")),
        "cast": list_to_str(movie.get("cast")),
        "director": list_to_str(movie.get("director")),
        "plot": movie.get("plot outline", "No plot available."),
        "poster": movie.get("full-size cover url"),
        "url": f"https://www.imdb.com/title/tt{movie_id}/"
    }
    return details

async def shorten_url(long_url: str):
    """Shortens a given URL using a predefined shortening service."""
    try:
        response = await fetch.get(f"https://api.shrtco.de/v2/shorten?url={long_url}")
        data = response.json()
        return data.get("result", {}).get("short_link", long_url)
    except Exception as e:
        logger.error(f"Error shortening URL: {e}")
        return long_url

def sanitize_filename(filename: str) -> str:
    """Removes invalid characters from filenames."""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def format_message(text: str, max_length: int = 4000):
    """Truncates a message if it exceeds the max length."""
    return text if len(text) <= max_length else text[:max_length] + "..."

async def delete_message(bot, chat_id, message_id, delay: int = 5):
    """Deletes a message after a given delay."""
    await asyncio.sleep(delay)
    await bot.delete_messages(chat_id, message_id)
