from info import BIN_CHANNEL, URL
from utils import temp
from web.utils.custom_dl import TGCustomYield
from utils import get_size
import urllib.parse
import secrets
import mimetypes
import aiofiles
import logging
import aiohttp

async def fetch_properties(message_id):
    media_msg = await temp.BOT.get_messages(BIN_CHANNEL, message_id)
    file_properties = await TGCustomYield().generate_file_properties(media_msg)
    file_name = file_properties.file_name if file_properties.file_name \
        else f"{secrets.token_hex(2)}.jpeg"
    mime_type = file_properties.mime_type if file_properties.mime_type \
        else f"{mimetypes.guess_type(file_name)}"
    return file_name, mime_type


async def render_page(message_id):
    file_name, mime_type = await fetch_properties(message_id)
    src = urllib.parse.urljoin(URL, str(message_id))
    audio_formats = ['audio/mpeg', 'audio/mp4', 'audio/x-mpegurl', 'audio/vnd.wav']
    video_formats = ['video/mp4', 'video/avi', 'video/ogg', 'video/h264', 'video/h265', 'video/x-matroska']
    if mime_type.lower() in video_formats:
        async with aiofiles.open('web/template/req.html') as r:
            heading = 'Watch {}'.format(file_name)
            tag = mime_type.split('/')[0].strip()
            html = (await r.read()).replace('tag', tag) % (heading, file_name, src)
    elif mime_type.lower() in audio_formats:
        async with aiofiles.open('web/template/req.html') as r:
            heading = 'Listen {}'.format(file_name)
            tag = mime_type.split('/')[0].strip()
            html = (await r.read()).replace('tag', tag) % (heading, file_name, src)
    else:
        async with aiofiles.open('web/template/dl.html') as r:
            async with aiohttp.ClientSession() as s:
                async with s.get(src) as u:
                    file_size = get_size(u.headers.get('Content-Length'))
                    html = (await r.read()) % (heading, file_name, src, file_size)
    current_url = f'{URL}{str(message_id)}'
    html_code = f'''
   <p>
    <center><h3>Click on 👇 button to watch in your favorite player or to Download</h3></center>
    <center>
        <button style="font-size: 20px; background-color: skyblue; border-radius: 10px;" onclick="window.location.href = 'intent:{current_url}#Intent;package=com.mxtech.videoplayer.ad;S.title={file_name};end'">MX player</button> &nbsp
        <button style="font-size: 20px; background-color: orange; border-radius: 10px;" onclick="window.location.href = 'vlc://{current_url}'">VLC player</button> &nbsp <br>
        <p>&nbsp</p>
        <button style="font-size: 20px; background-color: red; border-radius: 10px;" onclick="window.location.href = 'playit://playerv2/video?url={current_url}&amp;title={file_name}'">Playit player</button> &nbsp <br>
        <p>&nbsp</p>
        <button style="font-size: 20px; background-color: yellow; border-radius: 10px;" onclick="window.location.href = '{current_url}'">Download and Watch</button> &nbsp
    </center>
</p>
</p>
<center>
    <h2>
        <a href="https://telegram.me/isaimini_updates">
            <img src="https://graph.org/file/b57cdba982191a25db535.jpg" alt="isaimini" width="150" height="75">
        </a>
    </h2>
</center>

'''

    html += html_code
    return html
