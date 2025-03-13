import asyncio
import os
import threading
from collections import defaultdict, deque

import discord
from discord import FFmpegPCMAudio
from dotenv import load_dotenv

import plugins
from plugins.DataBase.mongo import (
    MongoDataBase
)
from plugins.Helpers.youtube_dl import get_best_info_media

load_dotenv()


class DataBases():

    def __init__(self):
        self.mongodb_client = self.__get_mongodb_client()

    @staticmethod
    def __get_mongodb_client():
        MONGODATABASE_USER = os.getenv('MONGODATABASE_USER', '')
        MONGODATABASE_PASSWORD = os.getenv('MONGODATABASE_PASSWORD', '')
        MONGODATABASE_HOST = os.getenv('MONGODATABASE_HOST', '')

        # client
        return MongoDataBase(host=MONGODATABASE_HOST, user=MONGODATABASE_USER, passwd=MONGODATABASE_PASSWORD)


class Cache():
    def __init__(self, databases: DataBases):
        # Cached guilds
        # self.guilds = {}
        #
        # query = {'_id': 0, 'id': 1, 'temporary': 1, 'members': 1}
        # for guild in databases.mongodb_client.get_documents(database_name='dbot', collection_name='guilds',
        #                                                     query=query):
        #     self.guilds[guild.get('id', '')] = guild

        # count of defaultdict - count inner dicts
        self.stats = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(deque)))))

        query = {'_id': 0, 'id': 1, 'xp': 1}
        for guild in databases.mongodb_client.get_documents(database_name='dbot', collection_name='guilds',
                                                            query=query):
            guild_xp = guild.get('xp', {})

            self.stats[guild.get('id', '')]['xp']['message_xp'] = guild_xp.get('message_xp', 100)
            self.stats[guild.get('id', '')]['xp']['voice_xp'] = guild_xp.get('voice_xp', 50)
            self.stats[guild.get('id', '')]['xp']['message_xp_delay'] = guild_xp.get('message_xp_delay', 60)
            self.stats[guild.get('id', '')]['xp']['message_xp_limit'] = guild_xp.get('message_xp_limit', 60)


class AudioSourceTracked(discord.AudioSource):
    def __init__(self, source, path, seconds=0):
        self._source = source
        self.path = path
        self.count_20ms = int(seconds / 0.02)
        # self.count_20ms = seconds

    def read(self) -> bytes:
        data = self._source.read()

        if data:
            self.count_20ms += 1

        return data

    @property
    def progress(self) -> float:
        return self.count_20ms * 0.02  # count_20ms * 20ms

class ResultThread(threading.Thread):
    def __init__(self, target: lambda: None):
        super().__init__()

        self.target = target
        self.result = None
        self.daemon = True

    def run(self):
        self.result = self.target()


def delete_slice(d: deque, start: int, stop: int):
    length = len(d)
    stop = min(stop, length) # don't go past the end
    start = min(start, stop) # don't go past stop
    if start < length // 2:
        d.rotate(-start)
        for i in range(stop-start): # use xrange on Python 2
            d.popleft()
        d.rotate(start)
    else:
        n = length - stop
        d.rotate(n)
        for i in range(stop - start):
            d.pop()
        d.rotate(-n)

def repeat(self, voice_client):
    audioSource = self.discordBot.audiosource
    ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                      'options': f'-vn -loglevel fatal'}
    audioSource = AudioSourceTracked(discord.FFmpegPCMAudio(audioSource.path, **ffmpeg_options), path=audioSource.path)
    self.discordBot.audiosource = audioSource
    voice_client.play(audioSource, after=lambda ex: repeat(self, voice_client))

dataBases = DataBases()
cache = Cache(dataBases)
# mongoDataBase = dataBases.mongodb_client

default_role = discord.PermissionOverwrite(
    view_channel=True,
    manage_channels=False,
    manage_permissions=False,
    manage_webhooks=False,
    create_instant_invite=True,
    send_messages=True,
    embed_links=True,
    attach_files=True,
    add_reactions=True,
    use_external_emojis=False,
    mention_everyone=False,
    manage_messages=False,
    read_message_history=True,
    send_tts_messages=False,
    # use_slash_commands=True,
    connect=True,
    speak=True,
    stream=True,
    use_voice_activation=True,
    priority_speaker=False,
    mute_members=False,
    deafen_members=False,
    move_members=False
)

owner_role = discord.PermissionOverwrite(
    view_channel=True,
    manage_channels=True,
    manage_permissions=True,
    manage_webhooks=True,
    create_instant_invite=True,
    send_messages=True,
    embed_links=True,
    attach_files=True,
    add_reactions=True,
    use_external_emojis=True,
    mention_everyone=True,
    manage_messages=True,
    read_message_history=True,
    send_tts_messages=True,
    # use_slash_commands=True,
    connect=True,
    speak=True,
    stream=True,
    use_voice_activation=True,
    priority_speaker=True,
    mute_members=True,
    deafen_members=True,
    move_members=True
)
