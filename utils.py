import asyncio
import logging
import os
import threading
from collections import defaultdict, deque

import discord
from discord import FFmpegPCMAudio, HTTPException, Forbidden
from dotenv import load_dotenv

from plugins.DataBase.mongo import (
    MongoDataBase
)

load_dotenv()


class EventSender():
    def __init__(self, discordBot):
        self.discordBot = discordBot

        # rate limiters
        self.global_semaphore = asyncio.Semaphore(5)  # allow up to 5 sends at once globally
        self.guild_locks = {}  # one lock per guild to serialize sends

    async def send_messages(self):
        await self.discordBot.client.wait_until_ready()

        while not self.discordBot.client.is_closed():
            # Launch one task per guild
            tasks = [self.send_guild_messages(guild_id) for guild_id in self.discordBot.events.keys()]
            if tasks:
                await asyncio.gather(*tasks)

            # Pause a bit before next full iteration
            await asyncio.sleep(2)

    async def send_guild_messages(self, guild_id):
        events = self.discordBot.events.get(guild_id, deque())
        if not events:
            return

        guild = self.discordBot.client.get_guild(guild_id)
        if not guild or not guild.system_channel:
            return

        system_channel = guild.system_channel

        # Create lock if it doesn't exist
        if guild_id not in self.guild_locks:
            self.guild_locks[guild_id] = asyncio.Lock()

        async with self.guild_locks[guild_id]:
            while events:
                # send in chunks of 10
                chunk = []
                for _ in range(min(10, len(events))):
                    chunk.append(events.popleft())

                if not chunk:
                    continue

                try:
                    # Limit global concurrency
                    async with self.global_semaphore:
                        await system_channel.send(embeds=chunk)
                        await asyncio.sleep(1.25)  # per-guild spacing
                except (HTTPException, Forbidden) as e:
                    logging.warning(f"[{guild.name}] Failed to send embeds: {e}")
                    await asyncio.sleep(2)  # backoff on error


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
    audioSource = AudioSourceTracked(FFmpegPCMAudio(audioSource.path, **ffmpeg_options), path=audioSource.path)
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
