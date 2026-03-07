import logging
import os
import subprocess
import re
from collections import deque
from pathlib import Path

#import streamlink
# import youtube_dl
import yt_dlp as youtube_dl
from yt_dlp import DownloadError, extractor
import requests

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

def is_supported_url_youtube(url):
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


def archive_search(title, result_count=1):
    """
        Search Internet Archive for downloadable music by title or artist.
        Returns a list of item URLs (default 1 result).
        """
    url = "https://archive.org/advancedsearch.php"
    params = {
        "q": f'title:({title}) AND mediatype:(audio) AND collection:(audio_music)',
        "fl[]": ["identifier", "title", "format"],
        "rows": result_count,
        "page": 1,
        "sort[]": "downloads desc",
        "output": "json"
    }

    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    urls = []
    for doc in data["response"]["docs"]:
        # Only add items with actual audio files
        if "format" in doc and any(f in doc["format"] for f in ["MP3", "VBR MP3", "FLAC"]):
            urls.append(f"https://archive.org/details/{doc['identifier']}")

    return urls


def get_best_info_media(title: str, ydl_opts=None, search_engine='Internet Archive', result_count=1, download=False):
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
            'socket_timeout': 10,
        }

    # ydl_opts['cookiefile'] = f"{Path(__file__).parent / 'cookies' / 'www.youtube.com_cookies.txt'}"

    if re.match(regex_link, title):
        url = title
    else:
        url = None

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.cache.remove()
        except (PermissionError, FileNotFoundError, OSError):
            return False

        if url:
            try:
                info = ydl.extract_info(url, download=download)
            except Exception as e:
                logging.warning(e)
                return False
        else:
            if search_engine:
                if search_engine == 'Internet Archive':
                    try:
                        archive_results = archive_search(title, result_count)
                        logging.info(f"Archive search results: {archive_results}")
                        for archive_url in archive_results:
                            info = ydl.extract_info(archive_url, download=download)

                            if info:
                                break

                        if not info:
                            return False
                    except Exception as e:
                        return False
                else:
                    info = ydl.extract_info(f"{search_engine}{result_count}:{title}", download=download)
            else:
                try:
                    info = ydl.extract_info(f"ytsearch{result_count}:{title}", download=download)
                except DownloadError as e:
                    logging.warning('DownloadError')
                    # info = None
                    return False

                # if not info:
                #     try:
                #         info = ydl.extract_info(f"scsearch{result_count}:{title}", download=download)
                #     except DownloadError:
                #         logging.warning('DownloadError')
                #         return False

    if not info:
        return False

    formatSelector = ydl.build_format_selector(ydl_opts.get('format'))

    bestFormats = []
    bestFormat = {}

    if 'entries' in info and len(info['entries']) != 0:
        for result in info['entries']:
            try:
                bestFormats.append(list(formatSelector(result))[0])
            except (KeyError, StopIteration, TypeError):
                bestFormats.append(result)
    else:
        try:
            bestFormat = list(formatSelector(info))[0]
        except (KeyError, StopIteration, TypeError):
            bestFormat = info

    if bestFormats:
        i = 0
        for format in bestFormats:
            ydl.add_extra_info(format, info['entries'][i])
            i += 1

        return bestFormats

    ydl.add_extra_info(bestFormat, info)

    return bestFormat
