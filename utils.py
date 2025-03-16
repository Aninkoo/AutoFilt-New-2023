import aiohttp
import json
import logging
from pyrogram.errors import InputUserDeactivated, UserNotParticipant, FloodWait, UserIsBlocked, PeerIdInvalid
from info import AUTH_CHANNEL, LONG_IMDB_DESCRIPTION, MAX_LIST_ELM, CUSTOM_FILE_CAPTION, UPDATES_CHNL, SHORTLINK_URL
from imdb import Cinemagoer 
import asyncio
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import enums
#from typing import Union
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

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

TOT_SHORT = len(SHORTLINK_URL)
tot_short = TOT_SHORT- 1

BTN_URL_REGEX = re.compile(
    r"(\[([^\[]+?)\]\((buttonurl|buttonalert):(?:/{0,2})(.+?)(:same)?\))"
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


# temp db for banned 
class temp(object):
    BANNED_USERS = []
    BANNED_CHATS = []
    ME = None
    CURRENT=int(os.environ.get("SKIP", 2))
    CANCEL = False
    MELCOW = {}
    FILES = {}
    U_NAME = None
    B_NAME = None
    SETTINGS = {}
    FILES_IDS = {}
    SPELL_CHECK = {}
    BOT = None

async def is_subscribed(bot, query):
    try:
        user = await bot.get_chat_member(AUTH_CHANNEL, query.from_user.id)
    except UserNotParticipant:
        pass
    except Exception as e:
        logger.exception(e)
    else:
        if user.status != enums.ChatMemberStatus.BANNED:
            return True

    return False

async def getEpisode(filename):
    match = re.search(r'(?ix)(?:E(\d{1,2})|S\d{1,2}E(\d{1,2})|Ep(\d{1,2})|episode (\d+))', filename)
    if match:
            return match.group(1) or match.group(2) or match.group(3) or match.group(4)

async def getSeason(filename):
    match = re.search(r'(?ix)(?:season (\d{1,2})|S(\d{1,2}))', filename)
    if match:
            return match.group(1) or match.group(2)

async def get_poster(query, bulk=False, id=False, file=None):
    if not id and query is not None:
        #query = (str(query).strip()).lower()
        
        query = (query.strip()).lower()
        title = query
        year = re.findall(r'[1-2]\d{3}$', query, re.IGNORECASE)
        if year:
            year = list_to_str(year[:1])
            title = (query.replace(year, "")).strip()
        elif file is not None:
            year = re.findall(r'[1-2]\d{3}', file, re.IGNORECASE)
            if year:
                year = list_to_str(year[:1]) 
        else:
            year = None
        movieid = imdb.search_movie(title.lower(), results=10)
        if not movieid:
            return None
        if year:
            filtered=list(filter(lambda k: str(k.get('year')) == str(year), movieid))
            if not filtered:
                filtered = movieid
        else:
            filtered = movieid
        movieid=list(filter(lambda k: k.get('kind') in ['movie', 'tv series'], filtered))
        if not movieid:
            movieid = filtered
        if bulk:
            return movieid
        movieid = movieid[0].movieID
    else:
        movieid = query
    movie = imdb.get_movie(movieid)
    if movie.get("original air date"):
        date = movie["original air date"]
    elif movie.get("year"):
        date = movie.get("year")
    else:
        date = "N/A"
    plot = ""
    if not LONG_IMDB_DESCRIPTION:
        plot = movie.get('plot')
        if plot and len(plot) > 0:
            plot = plot[0]
    else:
        plot = movie.get('plot outline')
    if plot and len(plot) > 800:
        plot = plot[0:800] + "..."

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
        "writer":list_to_str(movie.get("writer")),
        "producer":list_to_str(movie.get("producer")),
        "composer":list_to_str(movie.get("composer")) ,
        "cinematographer":list_to_str(movie.get("cinematographer")),
        "music_team": list_to_str(movie.get("music department")),
        "distributors": list_to_str(movie.get("distributors")),
        'release_date': date,
        'year': movie.get('year'),
        'genres': list_to_str(movie.get("genres")),
        'poster': movie.get('full-size cover url'),
        'plot': plot,
        'plots': movie.get('plot'),
        'rating': str(movie.get("rating")),
        'url':f'https://www.imdb.com/title/tt{movieid}'
    }

async def filter_dramas(query: str, max_retries: int = 20) -> str:
    """
    Searches for dramas with the external API using API_URL.
    Retries up to `max_retries` times if the result is empty.
    Returns the 'slug' of the best matching drama or movie (based on title similarity),
    excluding dramas or movies with a year greater than the current year.
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
                    if dramas:  # If dramas are found, proceed to find the best match
                        # Calculate similarity scores for each drama's title
                        best_match = None
                        best_score = 0  # Initialize with the lowest possible score

                        for drama in dramas:
                            year = drama.get("year", 0)  # Get the year, default to 0 if not available
                            # Skip dramas or movies with a year greater than the current year
                            if year > current_year:
                                continue

                            title = drama.get("title", "")
                            # Calculate similarity score between query and title
                            score = fuzz.ratio(query.lower(), title.lower())
                            # Update best match if the current score is higher
                            if score > best_score:
                                best_score = score
                                best_match = drama

                        # Return the 'slug' of the best matching drama
                        if best_match:
                            return best_match.get("slug", "")
                        else:
                            return ""  # No match found
                    else:  # If dramas are empty, retry
                        retries += 1
                        print(f"Retry {retries}: No results found. Retrying...")
                        await asyncio.sleep(1)  # Use asyncio.sleep instead of time.sleep
                else:
                    print(f"Error: API returned status code {response.status_code}")
                    retries += 1
                    await asyncio.sleep(1)  # Use asyncio.sleep instead of time.sleep
            except Exception as e:
                print(f"An error occurred: {e}")
                retries += 1
                await asyncio.sleep(1)  # Use asyncio.sleep instead of time.sleep

    print(f"Max retries ({max_retries}) reached. Returning empty string.")
    return ""  # Return an empty string if no results are found after retries    

async def broadcast_messages(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        await message.pin()
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await broadcast_messages(user_id, message)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id}-Removed from Database, since deleted account.")
        return False, "Deleted"
    except UserIsBlocked:
        logging.info(f"{user_id} -Blocked the bot.")
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id} - PeerIdInvalid")
        return False, "Error"
    except Exception as e:
        return False, "Error"

async def broadcast_messages_group(chat_id, message):
    try:
        kd = await message.copy(chat_id=chat_id)
        try:
            await kd.pin()
        except:
            pass
        return True, "Succes"
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await broadcast_messages_group(chat_id, message)
    except Exception as e:
        return False, "Error"

async def search_gagala(text):
    usr_agent = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/61.0.3163.100 Safari/537.36'
        }
    text = text.replace(" ", '+')
    url = f'https://www.google.com/search?q={text}'
    response = requests.get(url, headers=usr_agent)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    titles = soup.find_all( 'h3' )
    return [title.getText() for title in titles]


async def get_settings(group_id):
    settings = temp.SETTINGS.get(group_id)
    if not settings:
        settings = await db.get_settings(group_id)
        temp.SETTINGS[group_id] = settings
    return settings
    
async def save_group_settings(group_id, key, value):
    current = await get_settings(group_id)
    current[key] = value
    temp.SETTINGS[group_id] = current
    await db.update_settings(group_id, current)
    
def get_size(size):
    """Get size in readable format"""

    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

def split_list(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]  

def get_file_id(msg: Message):
    if msg.media:
        for message_type in (
            "photo",
            "animation",
            "audio",
            "document",
            "video",
            "video_note",
            "voice",
            "sticker"
        ):
            obj = getattr(msg, message_type)
            if obj:
                setattr(obj, "message_type", message_type)
                return obj

def extract_user(message: Message) -> Union[int, str]:
    """extracts the user from a message"""
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
            # don't want to make a request -_-
            user_first_name = user_id
        try:
            user_id = int(user_id)
        except ValueError:
            pass
    else:
        user_id = message.from_user.id
        user_first_name = message.from_user.first_name
    return (user_id, user_first_name)

def list_to_str(k):
    if not k:
        return "N/A"
    elif len(k) == 1:
        return str(k[0])
    elif MAX_LIST_ELM:
        k = k[:int(MAX_LIST_ELM)]
        return ' '.join(f'{elem}, ' for elem in k)
    else:
        return ' '.join(f'{elem}, ' for elem in k)

def last_online(from_user):
    time = ""
    if from_user.is_bot:
        time += "🤖 Bot :("
    elif from_user.status == enums.UserStatus.RECENTLY:
        time += "Recently"
    elif from_user.status == enums.UserStatus.LAST_WEEK:
        time += "Within the last week"
    elif from_user.status == enums.UserStatus.LAST_MONTH:
        time += "Within the last month"
    elif from_user.status == enums.UserStatus.LONG_AGO:
        time += "A long time ago :("
    elif from_user.status == enums.UserStatus.ONLINE:
        time += "Currently Online"
    elif from_user.status == enums.UserStatus.OFFLINE:
        time += from_user.last_online_date.strftime("%a, %d %b %Y, %H:%M:%S")
    return time


def split_quotes(text: str) -> List:
    if not any(text.startswith(char) for char in START_CHAR):
        return text.split(None, 1)
    counter = 1  # ignore first char -> is some kind of quote
    while counter < len(text):
        if text[counter] == "\\":
            counter += 1
        elif text[counter] == text[0] or (text[0] == SMART_OPEN and text[counter] == SMART_CLOSE):
            break
        counter += 1
    else:
        return text.split(None, 1)

    # 1 to avoid starting quote, and counter is exclusive so avoids ending
    key = remove_escapes(text[1:counter].strip())
    # index will be in range, or `else` would have been executed and returned
    rest = text[counter + 1:].strip()
    if not key:
        key = text[0] + text[0]
    return list(filter(None, [key, rest]))

def gfilterparser(text, keyword):
    if "buttonalert" in text:
        text = (text.replace("\n", "\\n").replace("\t", "\\t"))
    buttons = []
    note_data = ""
    prev = 0
    i = 0
    alerts = []
    for match in BTN_URL_REGEX.finditer(text):
        # Check if btnurl is escaped
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and text[to_check] == "\\":
            n_escapes += 1
            to_check -= 1

        # if even, not escaped -> create button
        if n_escapes % 2 == 0:
            note_data += text[prev:match.start(1)]
            prev = match.end(1)
            if match.group(3) == "buttonalert":
                # create a thruple with button label, url, and newline status
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

    try:
        return note_data, buttons, alerts
    except:
        return note_data, buttons, None

def parser(text, keyword):
    if "buttonalert" in text:
        text = (text.replace("\n", "\\n").replace("\t", "\\t"))
    buttons = []
    note_data = ""
    prev = 0
    i = 0
    alerts = []
    for match in BTN_URL_REGEX.finditer(text):
        # Check if btnurl is escaped
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and text[to_check] == "\\":
            n_escapes += 1
            to_check -= 1

        # if even, not escaped -> create button
        if n_escapes % 2 == 0:
            note_data += text[prev:match.start(1)]
            prev = match.end(1)
            if match.group(3) == "buttonalert":
                # create a thruple with button label, url, and newline status
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

    try:
        return note_data, buttons, alerts
    except:
        return note_data, buttons, None

def remove_escapes(text: str) -> str:
    res = ""
    is_escaped = False
    for counter in range(len(text)):
        if is_escaped:
            res += text[counter]
            is_escaped = False
        elif text[counter] == "\\":
            is_escaped = True
        else:
            res += text[counter]
    return res

async def send_react(chat_info, message):
    available_reactions = chat_info.available_reactions
    
    full_emoji_set = {
        "🙏",
        "🤗",
        "👾",
        "🤝",
        "🎉",
        "🌚",
        "👨‍💻",
        "😎",
        "😇",
        "🕊",
        "💘",
        "🔥",
        "🥰",
        "🗿",
        "❤️‍🔥",
        "🍾",
        "🎃",
        "👻",
        "🏆",
        "☃️",
        "💯",
        "⚡",
        "🙈",
        "😘",
        "🤩",
        "😍",
    }
    if available_reactions:
        if getattr(available_reactions, "all_are_enabled", False):
            emojis = full_emoji_set
        else:
            emojis = {
                reaction.emoji for reaction in available_reactions.reactions
            }
        await message.react(choice(list(emojis)), big=True)

async def get_verify_status(user_id):
    verify = await db.get_verify_status(user_id)
    return verify

async def update_verify_status(user_id, verify_token="", is_verified=False, verified_time=0, link="", no_short=None):
    current = await get_verify_status(user_id)
    current['verify_token'] = verify_token
    current['is_verified'] = is_verified
    current['verified_time'] = verified_time
    current['link'] = link
    if no_short is not None:
        if no_short > tot_short:
            no_short = 0
        current['no_short'] = no_short
    await db.update_verify_status(user_id, current)
    

async def get_shortlink(url, api, link):
    shortzy = Shortzy(api_key=api, base_site=url)
    link = await shortzy.convert(link)
    return link

def get_readable_time(seconds):
    periods = [('day', 86400), ('hours', 3600), ('mins', 60), ('secs', 1)]
    result = ''
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result += f'{int(period_value)}{period_name}'
    return result

async def add_chnl_message(file_name):
    pattern = [
        (r'^([\w\s-]+)\s(S\d{2})\s?(E(P|p)|E)\d{2}\s'),
        (r'^([\w\.-]+)\.(S\d{2})(E(P|p)|E|e)\d{2}\.'),
        (r'^([\w\s]+)\s(\d{4})\s(.*?)\s'),
        (r'^([\w\.]+)\.(\d{4})\.(.*?)\.')
    ]
    
    for pat in pattern:
        match = re.match(pat, file_name)
        if match:
            movie_name = match.group(1)
            year = match.group(2) if len(match.groups()) > 1  else None
            mov_name = file_name.lower()
            list1 = []
            language_keywords = ["tamil", "telugu", "malayalam", "kannada", "english", "hindi", "korean", "japanese"]
            episode = await getEpisode(file_name)
            if episode:
                return movie_name, year, None
            for lang in language_keywords:
                substring_index = mov_name.find(lang)
                if substring_index != -1:
                    capitalized_lang = lang.capitalize()
                    list1.append(capitalized_lang.strip())
            if len(list1) >= 1:
                if (movie_name, list1[0]) in update_list:
                    return None, None, None
            else:
                if (movie_name, 'No Lang') in update_list:
                    return None, None, None
            if len(list1) >= 1:
                update_list.add((movie_name, list1[0]))
                return movie_name, year, list1
            else:
                update_list.add((movie_name, 'No Lang'))
                return movie_name, year, None
    else:
        return None, None, None

def humanbytes(size):
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

async def send_all(bot, userid, files, ident):
    for file in files:
        f_caption = file.caption
        title = file.file_name
        size = get_size(file.file_size)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                        file_size='' if size is None else size,
                                                        file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                print(e)
                f_caption = f_caption
        if f_caption is None:
            f_caption = f"{title}"
        await bot.send_cached_media(
            chat_id=userid,
            file_id=file.file_id,
            caption=f_caption,
            protect_content=True if ident == "filep" else False,
            reply_markup=InlineKeyboardMarkup( [ [ InlineKeyboardButton('⚔️ 𝖯𝖨𝖱𝖮 𝖴𝖯𝖣𝖠𝖳𝖤𝖲 ⚔️', url="https://t.me/piroxbots") ] ] ))
