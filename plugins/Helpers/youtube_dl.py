import logging
import os
import subprocess
import re
#import streamlink
# import youtube_dl
import yt_dlp as youtube_dl
from yt_dlp import DownloadError, extractor

from datetime import datetime
from datetime import timedelta
# from youtube_dl import DownloadError
#from streamlink import NoPluginError, PluginError, StreamlinkError, NoStreamsError, StreamError

regex_link = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

ydl_opts = {
    'format': 'best',
    'quiet': False,
    'ignoreerrors': True,
    'noplaylist': True,
}

ydl_opts_youtube = {
    'format': 'bestvideo+bestaudio/best',
    # 'format': 'bestvideo[filesize<50M]+bestaudio/best[filesize<50M]',
    # '-outtmpl': '-',
    # 'format': 'worst',
    # 'postprocessors': [{
    #   'key': 'FFmpegExtractAudio',
    #   'preferredcodec': 'mp3',
    #   'preferredquality': '192',
    # }],
    'quiet': False,
    'ignoreerrors': True,
    # 'update': True,
    # 'max_downloads': 3,
    # 'socket_timeout': '13',
    # 'geo_bypass': True,
    # 'geo_bypass_country': True,
    # 'geo_bypass_ip_block': True,
    # 'verbose': True,
    'noplaylist': True,
}

ydl_opts_soundcloud = {
    'format': 'bestaudio/best',
    'quiet': False,
    'ignoreerrors': True,
    'noplaylist': True,
}

async def is_supported_url_youtube(url):
    """
    Check if url is supported by youtube_dl
    :param url:
    :return:
    """
    extractors = youtube_dl.extractor.gen_extractors()
    for e in extractors:
        if e.suitable(url) and e.IE_NAME != 'generic':
            return True
    return False


async def get_info_media(title: str, ydl_opts=None, search_engine=None, result_count=1, download=False):
    """

    :param title:
    :param ydl_opts:
    :param search_engine:
    :param result_count:
    :return:
    """
    if ydl_opts is None:
        ydl_opts = {
            # 'format': 'best[ext!=wav]/best',
            'quiet': False,
            'ignoreerrors': True,
            'noplaylist': True,
        }

    if re.match(regex_link, title):
        url = title
    else:
        url = None

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.cache.remove()

        if url:
            try:
                info = ydl.extract_info(url, download=download)
            except DownloadError:
                logging.warning('DownloadError')
                return False
        else:
            if search_engine:
                info = ydl.extract_info(f"{search_engine}{result_count}:{title}", download=download)
            else:
                try:
                    info = ydl.extract_info(f"ytsearch{result_count}:{title}", download=download)
                except DownloadError:
                    try:
                        info = ydl.extract_info(f"scsearch{result_count}:{title}", download=download)
                    except DownloadError:
                        logging.warning('DownloadError')
                        return False

    if not info:
        return

    if info['entries']:
        return info['entries']
    else:
        return info


async def get_best_info_media(title: str, ydl_opts=None, search_engine=None, result_count=1, download=False):
    """

    :param title:
    :param ydl_opts:
    :param search_engine:
    :param result_count:
    :return:
    """
    if ydl_opts is None:
        ydl_opts = {
            # 'format': 'best[ext!=wav]/best',
            'format': 'bestaudio/best',
            'quiet': False,
            'ignoreerrors': True,
            'noplaylist': True,
        }

    if re.match(regex_link, title):
        url = title
    else:
        url = None

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.cache.remove()

        if url:
            # if 'youtube.com' in url or 'youtu.be' in url:
            #    print('Youtube')
            # if is_supported_url_youtube(url=url):
            try:
                info = ydl.extract_info(url, download=download)
            except Exception as e:
                logging.warning(e)
                return False
                # else:
                #    print('Not supported url')
                #    return False
            """
            elif 'twitch.tv' in url:
                print('Twitch')
                session = streamlink.Streamlink()

                try:
                    streams = session.streams(url)
                except (NoPluginError, PluginError, StreamlinkError, NoStreamsError, StreamError):
                    print('StreamlinkError')
                    return False

                session.set_option("--twitch-disable-ads", "")
                session.set_option("--twitch-low-latency", "")
                print(streams, streams['best'])
                info = {'url': streams['best'].url,
                        'extractor': 'twitch'}
                # print(info['url'])

                return info
            """
        else:
            if search_engine:
                info = ydl.extract_info(f"{search_engine}{result_count}:{title}", download=download)
            else:
                try:
                    info = ydl.extract_info(f"ytsearch{result_count}:{title}", download=download)
                except DownloadError:
                    try:
                        info = ydl.extract_info(f"scsearch{result_count}:{title}", download=download)
                    except DownloadError:
                        logging.warning('DownloadError')
                        return False
    if not info:
        return False

    # print(info)
    # if 'entries' in info:
    #    if len(info['entries']) > 0:
    #        info = info['entries'][0]

    # ydl.list_formats(info)

    formatSelector = ydl.build_format_selector(ydl_opts.get('format'))

    bestFormats = []
    bestFormat = {}

    if 'entries' in info and len(info['entries']) != 0:
        for result in info['entries']:
            try:
                bestFormats.append(list(formatSelector(result))[0])
            except (KeyError, StopIteration):
                bestFormats.append(result)
    else:
        try:
            bestFormat = list(formatSelector(info))[0]
        except (KeyError, StopIteration):
            bestFormat = info

    if bestFormats:
        i = 0
        for format in bestFormats:
            ydl.add_extra_info(format, info['entries'][i])
            i += 1

        return bestFormats

    ydl.add_extra_info(bestFormat, info)

    return bestFormat


# title = 'https://www.youtube.com/watch?v=45ZkW-m91VA'
# ydl_opts = ydl_opts_youtube
# ydl_opts = ydl_opts_soundcloud
# search_engine = 'ytsearch'
# search_engine = 'scsearch'

# info = get_best_info_media(title=title)#, ydl_opts=ydl_opts)#, search_engine='scsearch')
# print(info)
# print(info)
# print(info['url'])
# print(info['thumbnails'])

# ytthumbnail_url = [thumbnail['url'] for thumbnail in info['thumbnails'] if thumbnail['id'] == str((len(info['thumbnails'])-1))]
# scthumbnail_url = [thumbnail['url'] for thumbnail in info['thumbnails'] if thumbnail['id'] == 'original']
# if ytthumbnail_url:
#    thumbnail_url = ytthumbnail_url[0]
# else:
#    thumbnail_url = scthumbnail_url[0]
# print(thumbnail_url)

"""
# if any link will do 
urls = [format['url'] for format in r['formats']]

# if you want links with video and audio
urls = [f['url'] for f in r['formats'] if f['acodec'] != 'none' and f['vcodec'] != 'none']

url = info['url']

url = url.split('videoplayback?', 1)[1].split('&')
url = url[0].split('=', 1)[1]

now = datetime.now()
works_to = datetime.fromtimestamp(int(url))
print(works_to - now)
if works_to > now:
    print('link working')
else:
    print('link not working')
"""
# expire = urls.split('?expire=', 1)[1].split('&', 1)[0]
# print(expire)
# for item in url:
#    print(f"{item.split('=')[0]} = {item.split('=')[1]}")
