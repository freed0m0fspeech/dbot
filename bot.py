# IMPORTS --------------------------------------------------------------------------------------------------------------


import asyncio
import datetime
import json
import math
import os
import re
import aiohttp
import discord
import requests
import youtube_dl
import yt_dlp
import time
import random
import xml.etree.ElementTree as ET
import io

from discord.ext import commands
from dotenv import load_dotenv
from pymongo import MongoClient, errors, ReturnDocument
from pymongo.server_api import ServerApi
from discord import FFmpegPCMAudio
from discord.utils import get
from dateutil.relativedelta import relativedelta
from twitchAPI.twitch import Twitch
from twitchAPI.webhook import TwitchWebHook
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.types import AuthScope
from pprint import pprint
from uuid import UUID
from discord_slash import SlashCommand
from discord_slash.utils import manage_commands
from discord_slash import SlashCommandOptionType
from version import __version__

# VARIABLES ------------------------------------------------------------------------------------------------------------

# load_dotenv()

mongodb_username = os.getenv('mongodb_username')
mongodb_password = os.getenv('mongodb_password')


# BASIC FUNCTIONS ------------------------------------------------------------------------------------------------------


async def determine_prefix(ctx, message):
    guild = message.guild

    if guild:
        try:
            mongodb_guild = mongodb_client.bot.guilds.find_one({'guildID': guild.id}, {'prefix': 1, '_id': 0})
        except errors.OperationFailure:
            return os.getenv('prefix')

        return mongodb_guild['prefix']
    else:
        return os.getenv('prefix')


def get_connection_to_mongodb(user, passwd):
    try:
        mdb_client = MongoClient(
            f"mongodb+srv://{user}:{passwd}@botcluster.iy7wi.mongodb.net/bot?retryWrites=true&w=majority", server_api=ServerApi('1'))

        mdb_client.server_info()
    except errors.ConnectionFailure:
        mdb_client = None

    return mdb_client


def load_data_from_mongodb(db_client):
    try:
        data_base = db_client.get_database('bot')
        init = data_base.get_collection('init')

        # if init:
        data = init.find_one({}, {'_id': 0, 'token': 1, 'prefix': 1})
        os.environ['token'] = data.get('token', '')
        # os.environ["token_test"] = data['token_test']
        os.environ['prefix'] = data.get('prefix', '')
    except errors.OperationFailure:
        pass


# INITIALIZATION -------------------------------------------------------------------------------------------------------

regex = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

mongodb_client = get_connection_to_mongodb(mongodb_username, mongodb_password)

load_data_from_mongodb(mongodb_client)

# intents = discord.Intents.default()
# intents.members = True
client = commands.Bot(command_prefix=determine_prefix, intents=discord.Intents.all())
slash = SlashCommand(client, sync_commands=True)#, delete_from_unused_guilds=True)

client.remove_command('help')

# %TEMP%
if not discord.opus.is_loaded():
    discord.opus.load_opus('./libopus.so.0.8.0')


# %PROBLEM%
# start_time = datetime.datetime.now().time().strftime('%c')


# ASYNC FUNCTIONS ------------------------------------------------------------------------------------------------------


async def get_quote():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://zenquotes.io/api/random') as response:
            if response.status == 200:
                json_text = await response.text()
                json_data = json.loads(json_text)
                quote_text = json_data[0]['q'] + ' (' + json_data[0]['a'] + ')'

    return quote_text


async def get_horoscope(horo_sign):
    async with aiohttp.ClientSession() as session:
        async with session.get('https://ignio.com/r/export/utf/xml/daily/com.xml') as response:
            if response.status == 200:
                string_xml = await response.text()
                horoscope = ET.fromstring(string_xml)
                #  for sign in horoscope.findall('aries'):
                text = ''
                for sign in horoscope:
                    if sign.tag == 'date':
                        continue

                    if sign.tag == horo_sign:
                        # string = ''
                        for day in sign:
                            if day.tag == 'today':
                                # string += day.tag + ':' + day.text
                                return sign.tag + ': ' + day.text


async def is_moderator(ctx, author: discord.Member):
    guild = ctx.guild
    try:
        mongodb_guild = mongodb_client.bot.guilds.find_one({'guildID': ctx.guild.id}, {'moderators': 1, '_id': 0})
    except errors.OperationFailure:
        return False

    moderators = mongodb_guild.get('moderators')

    if moderators:
        for moderator in moderators:
            if author.top_role >= guild.get_role(moderator):
                return True

    return False


async def is_eligible(author: discord.Member, member: discord.Member):
    if author.top_role <= member.top_role:
        return False

    return True


async def has_mute_permission(member: discord.Member):
    if member.guild_permissions.mute_members:
        return True

    return False


async def has_deafen_permission(member: discord.Member):
    if member.guild_permissions.deafen_members:
        return True

    return False


async def has_move_permission(member: discord.Member):
    if member.guild_permissions.move_members:
        return True

    return False


async def is_command_chat(message):
    message_channel_id = message.channel.id

    try:
        mongodb_guild = mongodb_client.bot.guilds.find_one({'guildID': message.guild.id},
                                                           {"no_command_channel_id's": 1, '_id': 0})
    except errors.OperationFailure:
        return False

    no_command_channel_ids = mongodb_guild.get("no_command_channel_id's")

    if no_command_channel_ids:
        for no_command_channel_id in no_command_channel_ids:
            if message_channel_id == no_command_channel_id:
                return False

    return True


async def get_system_channel(guild: discord.guild):
    try:
        mongodb_guild = mongodb_client.bot.guilds.find_one({'guildID': guild.id}, {'system_channel': 1, '_id': 0})
    except errors.OperationFailure:
        return None

    system_channel_id = mongodb_guild.get('system_channel')

    if system_channel_id:
        try:
            system_channel = get(client.get_all_channels(), id=system_channel_id)
        except:
            system_channel = None

        return system_channel

    return None


async def get_videos_youtube(ctx, message):
    ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            # 'outtmpl': '%(id)s%(ext)s',
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

    videos = {}
    # max_downloads = 10

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        if re.match(regex, f'{message}'):
            info = ydl.extract_info(message, download=False)
        else:
            info = ydl.extract_info(f"ytsearch:{message}", download=False)

        if 'entries' in info:
            # info = ydl.extract_info(f'{message}', download=False)
            # for i, item in enumerate(info['entries']):
            for video in info['entries']:
                # if max_downloads == 0:
                #    break
                """
                data = {'url': info['entries'][i]['url'],
                        'webpage_url': info['entries'][i]['webpage_url'],
                        'channel_url': info['entries'][i]['channel_url'],
                        'thumbnail_url': info['entries'][i]['thumbnails'][len(info['entries'][i]['thumbnails']) - 1]['url'],
                        'userID': ctx.author.id,
                        'channel': info['entries'][i]['uploader'],
                        'duration': info['entries'][i]['duration']}
                """
                data = {'url': video['url'],
                        'webpage_url': video['webpage_url'],
                        'channel_url': video['channel_url'],
                        'thumbnail_url': video['thumbnails'][len(video['thumbnails']) - 1]['url'],
                        'userID': ctx.author.id,
                        'channel': video['uploader'],
                        'duration': video['duration']}
                videos[f"{video['title']}"] = data

                # videos.append(info['entries'][i]['url'])
        else:
            data = {'url': info['url'],
                    'webpage_url': info['webpage_url'],
                    'channel_url': info['channel_url'],
                    'thumbnail_url': info['thumbnails'][len(info['thumbnails']) - 1]['url'],
                    'userID': ctx.author.id,
                    'channel': info['uploader'],
                    'duration': info['duration']}
            videos[f"{info['title']}"] = data
            # videos.append(info['formats'][0]['url'])

    try:
        for title, data in videos.items():
            mongodb_client.bot.guilds.find_one_and_update({'guildID': ctx.guild.id},
                                                          {'$push':
                                                               {'music.music_queue':
                                                                    {'title': title,
                                                                     'url': data['url'],
                                                                     'webpage_url': data['webpage_url'],
                                                                     'channel_url': data['channel_url'],
                                                                     'thumbnail_url': data['thumbnail_url'],
                                                                     'userID': data['userID'],
                                                                     'channel': data['channel'],
                                                                     'duration': data['duration']}
                                                                }
                                                           }, upsert=True
                                                          )
    except errors.OperationFailure:
        return 0

    return len(videos)


async def get_playlist_youtube(ctx, message):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False,
        'ignoreerrors': True,
    }

    videos = {}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        if re.match(regex, f'{message}'):
            info = ydl.extract_info(message, download=False)

            if 'entries' in info:
                for video in info['entries']:
                    data = {'url': video['url'],
                            'webpage_url': video['webpage_url'],
                            'channel_url': video['channel_url'],
                            'thumbnail_url': video['thumbnails'][len(video['thumbnails']) - 1]['url'],
                            'userID': ctx.author.id,
                            'channel': video['uploader'],
                            'duration': video['duration']}
                    videos[f"{video['title']}"] = data

                try:
                    for title, data in videos.items():
                        mongodb_client.bot.guilds.find_one_and_update({'guildID': ctx.guild.id},
                                                                      {'$push':
                                                                           {'music.music_queue':
                                                                                {'title': title,
                                                                                 'url': data['url'],
                                                                                 'webpage_url': data['webpage_url'],
                                                                                 'channel_url': data['channel_url'],
                                                                                 'thumbnail_url': data['thumbnail_url'],
                                                                                 'userID': data['userID'],
                                                                                 'channel': data['channel'],
                                                                                 'duration': data['duration']}
                                                                            }
                                                                       }, upsert=True
                                                                      )
                except errors.OperationFailure:
                    return 0

    return len(videos)


# CLIENT EVENTS --------------------------------------------------------------------------------------------------------

#
@client.event
async def on_ready():
    # os.getenv('prefix')
    await client.change_presence(status=discord.Status.online,
                                 activity=discord.Game(f"/help in {len(client.guilds)} server(s) v{__version__}"))


@client.event
async def on_command_error(ctx, error):
    # if isinstance(error, CommandNotFound):
    await ctx.channel.send(f'{error}')

    raise error


@client.event
async def on_message(message):
    # if message.author == client.user:
    #    return

    if message.author.bot:
        return

    if message.mention_everyone:
        return

    # if not await is_command_chat(message):
    #    return

    if client.user.mentioned_in(message):
         await message.channel.send(
            f"Thanks for mention me. Type `{await determine_prefix(None, message)}help` for more information")

    # await client.process_commands(message)


@client.event
async def on_guild_join(guild):
    try:
        mongodb_client.bot.guilds.find_one_and_update({'guildID': guild.id}, {'$set': {'prefix': os.getenv('prefix')}},
                                                      upsert=True)
    except errors.OperationFailure:
        pass


# %PROBLEM%
@client.event
async def on_voice_state_update(member, before, after):
    # if member == client.user:
    #    return

    # if member.bot:
    #    return

    if not before.self_deaf == after.self_deaf:
        # print('self deaf')
        return

    if not before.self_mute == after.self_mute:
        # print('self mute')
        return

    if not before.self_video == after.self_video:
        # print('video')
        return

    if not before.self_stream == after.self_stream:
        # print('stream')
        return

    if not before.deaf == after.deaf:
        # print('deaf')
        return

    if not before.mute == after.mute:
        # print('mute')
        return
    mongodb_guilds = mongodb_client.bot.guilds
    # User join voice channel
    if after.channel is not None:
        # print('join')

        guild = member.guild
        mongodb_inits = mongodb_guilds.find_one({'guildID': guild.id}, {'temporary.category_init': 1, '_id': 0})

        inits = mongodb_inits['temporary']['category_init']

        if inits:
            if after.channel.id in inits:
                # print('new category')
                # admin_role = get(guild.roles, name="ADMINistrator")

                # mongodb_guild = mongodb_client.bot.guilds.find_one({'guildID': guild.id}, {'moderators': 1, 'administrators': 1, '_id': 0})

                # if after.channel.overwrites_for(guild.default_role).view_channel:
                #    view_channel = True
                # else:
                #    view_channel = False

                default_role = discord.PermissionOverwrite(view_channel=True,
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
                                                           move_members=False)

                overwrites = {
                    guild.default_role: default_role,
                    guild.me: discord.PermissionOverwrite(view_channel=True,
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
                                                          move_members=True)}
                """
                member: discord.PermissionOverwrite(view_channel=True,
                                                    manage_channels=True,
                                                    manage_permissions=False,
                                                    manage_webhooks=False,
                                                    create_instant_invite=True,
                                                    send_messages=True,
                                                    embed_links=True,
                                                    attach_files=True,
                                                    add_reactions=True,
                                                    use_external_emojis=False,
                                                    mention_everyone=False,
                                                    manage_messages=True,
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
                                                    move_members=False)
                """

                current_category = after.channel.category

                if current_category:
                    position = current_category.position
                else:
                    position = 0

                category = await guild.create_category(f'category-{member.name}', overwrites=overwrites,
                                                       position=position)
                text_channel = await category.create_text_channel(f'text-{member.name}')
                # nsfw_text_channel = await category.create_text_channel(f'🔞text-{member.name}-18', overwrites=overwrites, nsfw=True)
                voice_channel = await category.create_voice_channel(f'voice-{member.name}')

                await category.set_permissions(member, overwrite=default_role)

                # await text_channel.edit(sync_permissions=True)
                # await voice_channel.edit(sync_permissions=True)

                await member.move_to(channel=voice_channel)

                await text_channel.send(
                    f'This is temporary category. You can use allowed and category based commands (only for owner of category):\n'
                    f'/temporary category lock - lock|unlock category\n'
                    f'/temporary category invite_member @user - invite|kik member from category\n'
                    f'/temporary category invite_role @role - invite|kick role from category\n'
                    f'/temporary category disc_member @user - disconnect member\n'
                    f'/temporary category rename @name - change name of category\n'
                    f'/temporary category owner @user - check|set owner of category\n'
                    f'Use /help for information about commands')

                mongodb_guilds.find_one_and_update({'guildID': guild.id},
                                                   {'$addToSet':
                                                        {'temporary.categories': {'category_id': category.id,
                                                                                  'owner_id': member.id}}
                                                    },
                                                   upsert=True)
        else:
            return
    """
    else:
        # User leave voice channel
    """
    if before.channel:
        # User moved or leaves voice channel
        channel = before.channel
        category = channel.category
        members = channel.members
        if category:
            guild = channel.guild
            # User leaves channel last
            categories = mongodb_guilds.find_one({'guildID': guild.id, 'temporary.categories.category_id': category.id},
                                                 {'temporary.categories': 1, '_id': 0})
            if categories:
                if len(members) == 0:
                    # Leaves last member in voice channel
                    for text_channel in category.text_channels:
                        system_channel = await get_system_channel(guild)

                        if system_channel:
                            messages = await text_channel.history(limit=666, oldest_first=True).flatten()

                            history_of_messages = ''
                            for message in messages:
                                content = ''
                                author = message.author
                                if not message.attachments:
                                    content = author.name + '#' + author.discriminator + ': ' + message.content
                                else:
                                    for attachment in message.attachments:
                                        content += author.name + '#' + author.discriminator + ': ' + attachment.filename + ' (' + 'size:' + str(attachment.size) + ' bytes' + ' content:' + attachment.content_type + ' url:' + attachment.url + ' proxy_url:' +attachment.proxy_url + ') '

                                history_of_messages += str(message.created_at) + ' ' + content + '\n'

                            history_of_messages_bytes = bytes(history_of_messages, encoding='utf8')
                            data = io.BytesIO(history_of_messages_bytes)
                            await system_channel.send(file=discord.File(data, f'{str(datetime.datetime.now())}_{text_channel.name}.txt'))

                        await text_channel.delete()
                    for voice_channel in category.voice_channels:
                        await voice_channel.delete()

                        await category.delete()

                    mongodb_guilds.find_one_and_update({'guildID': guild.id},
                                                       {'$pull':
                                                            {'temporary.categories': {'category_id': category.id}}
                                                        })
                else:
                    if member.bot:
                        return
                    # Leaves not last member in voice channel
                    categories = list(
                        filter(lambda c: c['category_id'] == category.id, categories['temporary']['categories']))

                    if categories[0]['owner_id'] == member.id:
                        new_owner = None

                        for tmember in members:
                            if not tmember.bot:
                                new_owner = tmember

                        if not new_owner:
                            return

                        # for text_channel in category.text_channels:
                            # if text_channel.is_nsfw():
                            #    await text_channel.edit(name=f'🔞text-{new_owner.name}-18')
                            # else:
                        # await text_channel.edit(name=f'text-{new_owner.name}')
                        # await text_channel.send(f'\n<@{member.id}> was owner but left :(\nNew owner is <@{new_owner.id}> :)')

                        # for voice_channel in category.voice_channels:
                        #     await voice_channel.edit(name=f'voice-{new_owner.name}')

                        # await category.edit(name=f'category-{new_owner.name}')

                        default_role = discord.PermissionOverwrite(view_channel=True,
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
                                                                   move_members=False)

                        await category.set_permissions(new_owner, overwrite=default_role)

                        mongodb_guilds.find_one_and_update({'guildID': guild.id,
                                                            'temporary.categories.owner_id': member.id},
                                                           {'$set':
                                                                {'temporary.categories.$.owner_id': new_owner.id}
                                                            })


# %TEMP%
"""
@client.event
async def on_slash_command(ctx):
    return
"""


# COMMANDS -------------------------------------------------------------------------------------------------------------


# VOICE -----------------------------------------------------------------------------------------------------------
# .666.
guilds_ids = None


@slash.subcommand(base='voice',
                  base_description='Commands to interact with voice channel',
                  name='mute',
                  description="Mute or unmute someone in voice channel",
                  options=[manage_commands.create_option(
                      name="member",
                      description="Member to mute or unmute",
                      option_type=SlashCommandOptionType.USER,
                      required=True
                  )],
                  guild_ids=guilds_ids)
# @client.command()
async def voice_mute(ctx, member: discord.Member):
    await ctx.defer(hidden=True)

    if not ctx.guild.owner == ctx.author:
        if not await is_moderator(ctx, ctx.author):
            return await ctx.send(f"You are not moderator")
        if not await is_eligible(ctx.author, member):
            return await ctx.send(f"User is higher than you in hierarchy")
        if await has_mute_permission(member):
            return await ctx.send(f"User has mute permission and can't be muted")

    if member.voice:
        if member.voice.mute:
            await member.edit(mute=False)
            await ctx.send(f"<@{member.id}> is unmuted")
        else:
            await member.edit(mute=True)
            await ctx.send(f"<@{member.id}> is muted")
    else:
        await ctx.send(f"<@{member.id}>is not in voice channel")


@slash.subcommand(base='voice',
                  base_description='Commands to interact with voice channel',
                  name='deaf',
                  description="Deaf or undeaf someone in voice channel",
                  options=[manage_commands.create_option(
                      name="member",
                      description="Member to deaf or undeaf",
                      option_type=SlashCommandOptionType.USER,
                      required=True
                  )],
                  guild_ids=guilds_ids)
# @client.command()
async def voice_deaf(ctx, member: discord.Member):
    await ctx.defer(hidden=True)

    if not ctx.guild.owner == ctx.author:
        if not await is_moderator(ctx, ctx.author):
            return await ctx.send(f"You are not moderator")
        if not await is_eligible(ctx.author, member):
            return await ctx.send(f"User is higher than you in hierarchy")
        if await has_deafen_permission(member):
            return await ctx.send(f"User has deaf permission and can't be deaf")

    if member.voice:
        if member.voice.deaf:
            await member.edit(deafen=False)
            await ctx.send(f"<@{member.id}> is undeaf")
        else:
            await member.edit(deafen=True)
            await ctx.send(f"<@{member.id}> is deaf")
    else:
        await ctx.send(f"<@{member.id}>is not in voice channel")


@slash.subcommand(base='voice',
                  base_description='Commands to interact with voice channel',
                  name='disc',
                  description="Disconnect someone from voice channel",
                  options=[manage_commands.create_option(
                      name="member",
                      description="Member to disconnect",
                      option_type=SlashCommandOptionType.USER,
                      required=True
                  )],
                  guild_ids=guilds_ids)
# @client.command()
async def voice_disc(ctx, member: discord.Member):
    await ctx.defer(hidden=True)

    if not ctx.guild.owner == ctx.author:
        if not await is_moderator(ctx, ctx.author):
            return await ctx.send(f"You are not moderator")
        if not await is_eligible(ctx.author, member):
            return await ctx.send(f"User is higher than you in hierarchy")
        if await has_move_permission(member):
            return await ctx.send(f"User has move permission and can't be disconnected")

    if member.voice:
        await member.edit(voice_channel=None)
        await ctx.send(f"<@{member.id}> is disconnected")
    else:
        await ctx.send(f"<@{member.id}>is not in voice channel")


@slash.subcommand(base='voice',
                  base_description='Commands to interact with voice channel',
                  name='move',
                  description="Move someone in your voice channel",
                  options=[manage_commands.create_option(
                      name="member",
                      description="Member to move",
                      option_type=SlashCommandOptionType.USER,
                      required=True
                  )],
                  guild_ids=guilds_ids)
# @client.command()
async def voice_move(ctx, member: discord.Member):
    await ctx.defer(hidden=True)

    if not ctx.guild.owner == ctx.author:
        if not await is_moderator(ctx, ctx.author):
            return await ctx.send(f"You are not moderator")
        if not await is_eligible(ctx.author, member):
            return await ctx.send(f"User is higher than you in hierarchy")
        if await has_move_permission(member):
            return await ctx.send(f"User has move permission and can't be moved")

    if ctx.author.voice:
        voice_channel = ctx.author.voice.channel

        if member.voice:
            await member.move_to(channel=voice_channel)
            await ctx.send(f"<@{member.id}> is moved to {voice_channel.name}")
        else:
            await ctx.send(f"<@{member.id}>is not in voice channel")
    else:
        await ctx.send(f"Connect to voice channel before")


# MUSIC ----------------------------------------------------------------------------------------------------------------


@slash.subcommand(base='music',
                  name='skip',
                  description="Skip currently playing track",
                  options=[],
                  guild_ids=guilds_ids)
# @client.command()
async def music_skip(ctx):
    await ctx.defer()

    voice_client = ctx.guild.voice_client

    if not voice_client:
        await ctx.send('Not playing')
        return

    if voice_client.is_paused() or voice_client.is_playing():
        voice_client.stop()
        await ctx.send('Track skipped')
    else:
        await ctx.send('Not playing')


@slash.subcommand(base='music',
                  name='pause',
                  description="Pause or resume playing music",
                  options=[],
                  guild_ids=guilds_ids)
# @client.command()
async def music_pause(ctx):
    await ctx.defer()

    if ctx.guild.voice_client:
        voice_client = ctx.guild.voice_client
    else:
        await ctx.send('Not playing')
        return

    mongodb_guilds = mongodb_client.bot.guilds

    mongodb_guild = mongodb_guilds.find_one({'guildID': ctx.guild.id},
                                            {'music.now_playing.start_time': 1, 'music.now_playing.elapsed_time': 1,
                                             '_id': 0})

    try:
        now_playing = mongodb_guild['music']['now_playing']
    except KeyError:
        now_playing = None

    if voice_client.is_paused():
        voice_client.resume()
        await ctx.send('Track is resumed')

        if now_playing:
            mongodb_guilds.find_one_and_update({'guildID': ctx.guild.id},
                                               {'$set':
                                                    {'music.now_playing.start_time': datetime.datetime.now()}
                                                })
    elif voice_client.is_playing():
        voice_client.pause()
        await ctx.send('Track is paused')

        if now_playing:
            now_time = datetime.datetime.now()
            start_time = now_playing['start_time']
            elapsed_time = now_playing['elapsed_time']
            elapsed = now_time - start_time
            elapsed_seconds = (elapsed - datetime.timedelta(microseconds=elapsed.microseconds))

            if elapsed_time is not None:
                elapsed_seconds += datetime.timedelta(seconds=elapsed_time)

            mongodb_guilds.find_one_and_update({'guildID': ctx.guild.id},
                                               {'$set':
                                                    {'music.now_playing.elapsed_time': elapsed_seconds.seconds}
                                                })
    else:
        await ctx.send('Not playing')


"""
@client.command()
async def mvolume(ctx, volume):
    if ctx.voice_client:
        voice_client = ctx.voice_client
    else:
        return
    try:
        percentage_volume = float(int(volume)/100)
    except:
        percentage_volume = None

    print(percentage_volume)

    if percentage_volume:
        if percentage_volume <= 1 and percentage_volume >= 0:
            voice_client.source = discord.PCMVolumeTransformer(voice_client.source, volume=percentage_volume)
            await ctx.send(f"Music volume changed to {percentage_volume * 100}%")
"""


@slash.subcommand(base='music',
                  name='clear',
                  description="Clear music queue",
                  options=[manage_commands.create_option(
                      name="count",
                      description="Count of elements to delete (n > 0 from start, n < 0 from end)",
                      option_type=SlashCommandOptionType.INTEGER,
                      required=False
                  )],
                  guild_ids=guilds_ids)
# @client.command()
async def music_clear(ctx, count=0):
    await ctx.defer()

    if count == 0:
        mongodb_client.bot.guilds.find_one_and_update({'guildID': ctx.guild.id},
                                                      {'$unset': {'music.music_queue': 1}})
        return await ctx.send(f"Music queue was cleared")

    for i in range(abs(count)):
        mongodb_client.bot.guilds.find_one_and_update({'guildID': ctx.guild.id},
                                                      {'$pop': {'music.music_queue': int(-1 * math.copysign(1, count))}})

    return await ctx.send(f"{abs(count)} track(s) was cleared")


@slash.subcommand(base='music',
                  name='queue',
                  description="Show queue of the server",
                  options=[],
                  guild_ids=guilds_ids)
# @client.command()
async def music_queue(ctx):
    await ctx.defer()

    try:
        mongodb_guild = mongodb_client.bot.guilds.find_one({'guildID': ctx.guild.id},
                                                           {'music.music_queue': 1, '_id': 0})
    except errors.OperationFailure:
        return await ctx.send("Some problem with parsing queue. Try again later")

    duration_of_tracks = 0
    i = 0
    total_tracks = 0
    total_duration_of_tracks = 0

    try:
        music_queue = mongodb_guild['music']['music_queue']
    except KeyError:
        music_queue = None

    embeds = []
    page_number = 1
    count_of_sections = math.ceil(len(music_queue) / 20)

    if count_of_sections == 0:
        count_of_sections = 1

    # guild = mongodb_guilds.find_one({'guildID': ctx.guild.id})
    queue_embed = discord.Embed(title=f"Music queue ({ctx.guild.name}) - {len(music_queue)} total track(s)",
                                color=discord.Color.random(),
                                timestamp=datetime.datetime.utcnow())
    queue_embed.set_author(icon_url=client.user.avatar_url, name=client.user.name)
    for track in music_queue:
        if i % 20 == 0 and i != 0:
            queue_embed.set_footer(
                text=f"Page {page_number}/{count_of_sections}. ({datetime.timedelta(seconds=duration_of_tracks)}). All rights reserved by @©")
            embeds.append(queue_embed)
            page_number += 1
            duration_of_tracks = 0
            queue_embed = discord.Embed(title=f"Music queue ({ctx.guild.name})",
                                        color=discord.Color.random(),
                                        timestamp=datetime.datetime.utcnow())
            queue_embed.set_author(icon_url=client.user.avatar_url, name=client.user.name)

        i += 1
        total_tracks += 1
        total_duration_of_tracks += track['duration']
        duration_of_tracks += track['duration']
        queue_embed.add_field(name=f"({i}) {track['title']}",
                              value=f"{datetime.timedelta(seconds=track['duration'])}",
                              inline=False)

    queue_embed.set_footer(
        text=f"Page {page_number}/{count_of_sections}. ({datetime.timedelta(seconds=duration_of_tracks)}). All rights reserved by @©")

    embeds.append(queue_embed)

    embeds[0].title = f"Music queue ({ctx.guild.name}) - {len(music_queue)} total track(s) ({datetime.timedelta(seconds=total_duration_of_tracks)})"

    message = await ctx.send(content='Music queue', embed=embeds[0])
    await message.add_reaction('⏮')
    await message.add_reaction('◀')
    await message.add_reaction('▶')
    await message.add_reaction('⏭')

    def check(reaction, user):
        return user == ctx.author

    i = 0
    reaction = None
    if len(embeds) > 0:
        while True:
            if reaction:
                if message.id == reaction.message.id:
                    if str(reaction) == '⏮':
                        if i > 0:
                            i = 0
                            await message.edit(embed=embeds[i])
                    elif str(reaction) == '◀':
                        if i > 0:
                            i -= 1
                            await message.edit(embed=embeds[i])
                    elif str(reaction) == '▶':
                        if i < (len(embeds) - 1):
                            i += 1
                            await message.edit(embed=embeds[i])
                    elif str(reaction) == '⏭':
                        i = len(embeds) - 1
                        await message.edit(embed=embeds[i])

            try:
                reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
                await message.remove_reaction(reaction, user)
            except asyncio.exceptions.TimeoutError:
                break

    try:
        await message.clear_reactions()
    except discord.NotFound:
        print('Channel does not exist')


@slash.subcommand(base='music',
                  name='play',
                  description="Play music from music queue",
                  options=[manage_commands.create_option(
                      name="text",
                      description="Text to search or url on YouTube video",
                      option_type=SlashCommandOptionType.STRING,
                      required=False
                  )],
                  guild_ids=guilds_ids)
# @client.command()
async def music_play(ctx, text=None):
    await ctx.defer()
    if text:
        videos = await get_videos_youtube(ctx, text)

        if videos == 0:
            await ctx.send(f'Some problems with adding track(s)')
        else:
            await ctx.send(f'Added {videos} track(s)')

    author_voice = ctx.author.voice
    voice_client = ctx.guild.voice_client

    try:
        if author_voice:
            if not voice_client:
                voice_client = await author_voice.channel.connect(reconnect=True, timeout=10000)
            elif not voice_client.is_connected:
                voice_client = await voice_client.connect(reconnect=True, timeout=10000)
        else:
            return await ctx.send(f"Connect to voice channel to use this command")
    except TimeoutError:
        return await ctx.send(f"Timeout error")

    if voice_client.is_playing() or voice_client.is_paused():
        if not text:
            await ctx.send('I am already playing audio')
        return
    else:
        if not text:
            await ctx.send('Playing from queue')

        ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                          'options': '-vn'}

        while True:
            while voice_client.is_playing() or voice_client.is_paused():  # waits until song ends
                await asyncio.sleep(1)
            else:
                # Check if bot alone in voice channel or not
                members = voice_client.channel.members

                if len(members) == 1:
                    return await voice_client.disconnect()

                actual_members = 0

                for member in members:
                    if not member.bot:
                        actual_members += 1
                        break

                if actual_members == 0:
                    return await voice_client.disconnect()
                try:
                    guild = mongodb_client.bot.guilds.find_one_and_update({'guildID': ctx.guild.id},
                                                                          {'$pop': {'music.music_queue': -1}})
                except errors.OperationFailure:
                    guild = None

                try:
                    music = guild['music']['music_queue']
                except KeyError:
                    music = None

                if music:
                    mongodb_client.bot.guilds.find_one_and_update({'guildID': ctx.guild.id},
                                                                  {'$set':
                                                                       {'music.now_playing':
                                                                            {'title': music[0]['title'],
                                                                             'url': music[0]['url'],
                                                                             'webpage_url': music[0]['webpage_url'],
                                                                             'channel_url': music[0]['channel_url'],
                                                                             'thumbnail_url': music[0]['thumbnail_url'],
                                                                             'userID': music[0]['userID'],
                                                                             'channel': music[0]['channel'],
                                                                             'duration': music[0]['duration'],
                                                                             'start_time': datetime.datetime.now(),
                                                                             'elapsed_time': None}
                                                                        }
                                                                   }
                                                                  )
                    try:
                        voice_client.play(FFmpegPCMAudio(music[0]['url'], **ffmpeg_options))
                    except discord.ClientException:
                        await ctx.channel.send('Voice client is not connected')

                    member = get(client.get_all_members(), id=music[0]['userID'])

                    now_playing_embed = discord.Embed(title=f"{music[0]['title']}",
                                                      description=f"[{music[0]['channel']}]({music[0]['channel_url']})",
                                                      color=discord.Color.random(),
                                                      timestamp=datetime.datetime.utcnow(),
                                                      url=music[0]['webpage_url'])

                    now_playing_embed.add_field(name='Duration',
                                                value=f"{datetime.timedelta(seconds=music[0]['duration'])}",
                                                inline=True)

                    now_playing_embed.set_author(icon_url=client.user.avatar_url, name="Playing from queue")

                    if member.nick:
                        now_playing_embed.set_footer(icon_url=member.avatar_url,
                                                     text=f"Added by {member.nick}. All rights reserved by @©")
                    else:
                        now_playing_embed.set_footer(icon_url=member.avatar_url,
                                                     text=f"Added by {member.name}. All rights reserved by @©")

                    now_playing_embed.set_thumbnail(url=music[0]['thumbnail_url'])

                    await ctx.channel.send(embed=now_playing_embed)
                else:
                    mongodb_client.bot.guilds.find_one_and_update({'guildID': ctx.guild.id},
                                                                  {'$unset': {'music.now_playing': 1}})
                    return
                    # return await voice_client.disconnect()


@slash.subcommand(base='music',
                  name='now',
                  description="Show currently playing track",
                  options=[],
                  guild_ids=guilds_ids)
# @client.command()
async def music_now(ctx):
    await ctx.defer(hidden=True)

    now_time = datetime.datetime.now()
    mongo_db_guilds = mongodb_client.bot.guilds

    if ctx.guild.voice_client:
        voice_client = ctx.guild.voice_client
    else:
        await ctx.send('Not playing')
        return

    if not voice_client.is_playing() and not voice_client.is_paused():
        await ctx.send('Not playing')
        return

    mongodb_guild = mongo_db_guilds.find_one({'guildID': ctx.guild.id},
                                             {'music.now_playing': 1, '_id': 0})

    if mongodb_guild:
        now_playing = mongodb_guild['music']['now_playing']

        start_time = now_playing['start_time']
        elapsed_time = now_playing['elapsed_time']
        end_time = (now_time - start_time)

        if voice_client.is_paused():
            time_played = datetime.timedelta(seconds=elapsed_time)
        else:
            time_played = end_time - datetime.timedelta(microseconds=end_time.microseconds)
            if elapsed_time is not None:
                time_played += datetime.timedelta(seconds=elapsed_time)

        member = get(client.get_all_members(), id=now_playing['userID'])

        now_playing_embed = discord.Embed(title=f"{now_playing['title']}",
                                          description=f"[{now_playing['channel']}]({now_playing['channel_url']})",
                                          color=discord.Color.random(), timestamp=datetime.datetime.utcnow(),
                                          url=now_playing['webpage_url'])

        now_playing_embed.add_field(name='Duration',
                                    value=f"{time_played} of {datetime.timedelta(seconds=now_playing['duration'])}",
                                    inline=True)

        now_playing_embed.set_author(icon_url=client.user.avatar_url, name="Now playing")

        if member.nick:
            now_playing_embed.set_footer(icon_url=member.avatar_url,
                                         text=f"Added by {member.nick}. All rights reserved by @©")
        else:
            now_playing_embed.set_footer(icon_url=member.avatar_url,
                                         text=f"Added by {member.name}. All rights reserved by @©")

        now_playing_embed.set_thumbnail(url=now_playing['thumbnail_url'])

        await ctx.send(embed=now_playing_embed)
    else:
        await ctx.send('Not playing')


@slash.subcommand(base='music',
                  name='seek',
                  description="Go to position in currently playing track",
                  options=[manage_commands.create_option(
                      name="timestamp",
                      description="time you want to play from",
                      option_type=SlashCommandOptionType.STRING,
                      required=True
                  )],
                  guild_ids=guilds_ids)
# @client.command()
async def music_seek(ctx, timestamp):
    await ctx.defer(hidden=True)

    if ctx.guild.voice_client:
        voice_client = ctx.guild.voice_client
    else:
        await ctx.send('Not playing')
        return

    if not voice_client.is_playing() and not voice_client.is_paused():
        await ctx.send('Not playing')
        return

    mongodb_guilds = mongodb_client.bot.guilds

    mongodb_guild = mongodb_guilds.find_one({'guildID': ctx.guild.id}, {'music.now_playing': 1, '_id': 0})

    if mongodb_guild:
        now_playing = mongodb_guild['music']['now_playing']

        if now_playing['duration'] > 0:
            if now_playing['duration'] > 600:
                return await ctx.send(f"Command only allowed to tracks less than 10 minutes duration")

            try:
                timestamp = datetime.datetime.strptime(timestamp, '%H:%M:%S').time()
            except ValueError:
                return await ctx.send(f"Incorrect data format, should be 'H:M:S'. Example: 00:00:01")
                # raise ValueError("Incorrect data format, should be '%H:%M:%S'")

            ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                              'options': f'-vn -ss {timestamp}'}

            if voice_client.is_playing():
                voice_client.pause()

            voice_client.play(FFmpegPCMAudio(now_playing['url'], **ffmpeg_options))

            await ctx.send(f'Seeked to {timestamp} in track')

            if now_playing:
                mongodb_guilds.find_one_and_update({'guildID': ctx.guild.id},
                                                   {'$set':
                                                        {'music.now_playing.start_time': datetime.datetime.now(),
                                                         'music.now_playing.elapsed_time': timestamp.second + timestamp.minute * 60 + timestamp.hour * 3600}
                                                    })


# SERVER ---------------------------------------------------------------------------------------------------------------


@slash.slash(name='help',
             description="Show help message with all commands for bot",
             options=[manage_commands.create_option(
                 name="text",
                 description="Command name. Example: play",
                 option_type=SlashCommandOptionType.STRING,
                 required=False
             )],
             guild_ids=guilds_ids)
# @client.command()
async def help(ctx, text=None):
    await ctx.defer()

    try:
        sections = mongodb_client.bot.help
    except errors.OperationFailure:
        return await ctx.send(f"Some problem with parsing help. Try again later")

    # prefix = await determine_prefix(ctx, ctx.message)

    if text:
        for section in sections.find():
            for command in section['commands']:
                if command['command'] == text:
                    argument_string = ''

                    for argument in command['arguments']:
                        argument_string += ' <' + argument + '>'

                    embed = discord.Embed(title=f"{section['section']}", description=f"{section['description']}",
                                          color=discord.Color.random(), timestamp=datetime.datetime.utcnow())

                    embed.set_author(icon_url=client.user.avatar_url, name=client.user.name)
                    embed.set_footer(text="All rights reserved by @©")

                    embed.add_field(
                        # await determine_prefix(ctx, ctx.message)
                        name=f"{command['command']} {argument_string}",
                        value=f"{command['description']}", inline=True)
                    # embed.add_field(name="Allowed", value=f"{command['allowed']}", inline=True)
                    # embed.add_field(name="Denied", value=f"{command['denied']}", inline=True)

                    return await ctx.send(embed=embed)
    else:
        if sections:
            embeds = []

            page_number = 0
            count_of_sections = sections.count_documents({})

            for section in sections.find():
                page_number += 1
                embed = discord.Embed(title=f"{section['section']}", description=f"{section['description']}",
                                      color=discord.Color.random(), timestamp=datetime.datetime.utcnow())
                embed.set_author(icon_url=client.user.avatar_url, name=client.user.name)
                embed.set_footer(text=f"Page {page_number}/{count_of_sections}. All rights reserved by @©")

                for command in section['commands']:
                    argument_string = ''

                    for argument in command['arguments']:
                        argument_string += ' <' + argument + '>'

                    embed.add_field(
                        # await determine_prefix(ctx, ctx.message)}
                        name=f"{command['command']} {argument_string}",
                        value=f"{command['description']}",
                        inline=True)
                    # embed.add_field(name="Allowed",
                    #                value=f"{command['allowed']}",
                    #                inline=True)
                    # embed.add_field(name="Denied",
                    #                value=f"{command['denied']}",
                    #                inline=True)

                embeds.append(embed)

            embed = discord.Embed(title='Help',
                                  # await determine_prefix(ctx, ctx.message)
                                  description=f"/help <command> for information about some command",
                                  color=discord.Color.random(), timestamp=datetime.datetime.utcnow())

            embed.set_author(icon_url=client.user.avatar_url, name=client.user.name)
            embed.set_footer(text="All rights reserved by @©")

            message = await ctx.send(embed=embed)
            await message.add_reaction('⏮')
            await message.add_reaction('◀')
            await message.add_reaction('▶')
            await message.add_reaction('⏭')

            def check(reaction, user):
                return user == ctx.author

            i = -1
            reaction = None
            if len(embeds) > 0:
                while True:
                    if reaction:
                        if message.id == reaction.message.id:
                            if str(reaction) == '⏮':
                                if i > 0:
                                    i = 0
                                    await message.edit(embed=embeds[i])
                            elif str(reaction) == '◀':
                                if i > 0:
                                    i -= 1
                                    await message.edit(embed=embeds[i])
                            elif str(reaction) == '▶':
                                if i < (len(embeds) - 1):
                                    i += 1
                                    await message.edit(embed=embeds[i])
                            elif str(reaction) == '⏭':
                                i = len(embeds) - 1
                                await message.edit(embed=embeds[i])

                    try:
                        reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
                        await message.remove_reaction(reaction, user)
                    except asyncio.exceptions.TimeoutError:
                        break

            try:
                await message.clear_reactions()
            except discord.NotFound:
                print('Channel does not exist')

            return
    return await ctx.send(f"No commands found")


@slash.subcommand(base='fun',
                  name='quote',
                  description="Get random quote with author",
                  options=[],
                  guild_ids=guilds_ids)
# @client.command()
async def fun_quote(ctx):
    await ctx.defer(hidden=True)

    quote_text = await get_quote()
    await ctx.send(f"{quote_text}")


@slash.subcommand(base='fun',
                  name='horoscope',
                  description="Get horoscope for current day",
                  options=[manage_commands.create_option(
                      name="sign",
                      description="aries, taurus, gemini, cancer, leo, virgo, libra, scorpio, sagittarius, capricorn, aquarius, pisces",
                      option_type=SlashCommandOptionType.STRING,
                      required=True
                  )],
                  guild_ids=guilds_ids)
# @client.command()
async def fun_horoscope(ctx, sign):
    await ctx.defer(hidden=True)

    horoscope_text = await get_horoscope(sign)
    await ctx.send(f"{horoscope_text}")


@slash.subcommand(base='server',
                  name='members',
                  description="Get count of members on server",
                  options=[],
                  guild_ids=guilds_ids)
# @client.command()
async def server_members(ctx):
    await ctx.defer(hidden=True)

    guild = ctx.guild
    await ctx.send(f"{guild.member_count} members in {guild}")


@slash.subcommand(base='member',
                  name='avatar',
                  description="Get avatar of user",
                  options=[manage_commands.create_option(
                      name="member",
                      description="Member which avatar you want",
                      option_type=SlashCommandOptionType.USER,
                      required=True
                  ), manage_commands.create_option(
                      name="type",
                      description="Type of image you want [jpg, jpeg, gif, png, webp, gif]",
                      option_type=SlashCommandOptionType.STRING,
                      required=False
                  ), manage_commands.create_option(
                      name="size",
                      description="Size of image you want from 16 to 4096",
                      option_type=SlashCommandOptionType.INTEGER,
                      required=False
                  )],
                  guild_ids=guilds_ids)
# @client.command()
async def member_avatar(ctx, member: discord.Member, type=None, size=None):
    await ctx.defer(hidden=True)

    if size:
        if isinstance(size, int):
            if math.log(size, 2).is_integer():
                if 16 > size > 4096:
                    desired_size = None
            else:
                desired_size = None

    allowed_types = ['png', 'jpeg', 'webp', 'jpg', 'webp']

    if not type:
        if member.avatar.startswith('a_'):
            image_type = 'gif'
        else:
            image_type = 'webp'
    else:
        if not any([substring in type for substring in allowed_types]):
            image_type = 'webp'

    # print(member.avatar_url_as(format=None, size=desired_size))
    await ctx.send(
        f"https://cdn.discordapp.com/avatars/{member.id}/{member.avatar}.{type}?size={size}")


@slash.subcommand(base='server',
                  name='prefix',
                  description="Changing prefix on server",
                  options=[manage_commands.create_option(
                      name="new_prefix",
                      description="New prefix on server",
                      option_type=SlashCommandOptionType.STRING,
                      required=True
                  )],
                  guild_ids=guilds_ids)
# @client.command()
async def server_prefix(ctx, new_prefix):
    await ctx.defer(hidden=True)

    if not ctx.author.id == ctx.guild.owner_id:
        await ctx.send(f"Command can only be used by owner of the server")

    try:
        mongodb_client.bot.guilds.find_one_and_update({'guildID': ctx.guild.id},
                                                      {'$set': {'prefix': f'{new_prefix}'}},
                                                      upsert=True)  # , return_document=ReturnDocument.AFTER)

        await ctx.send(f"Prefix `{new_prefix}` is set")
    except errors.OperationFailure:
        await ctx.send(f"Some problem with changing prefix. Try again later")


@slash.subcommand(base='server',
                  subcommand_group='init',
                  name='moderator',
                  description="Add/delete moderator for bot",
                  options=[manage_commands.create_option(
                      name="role",
                      description="Role you want add to moderators",
                      option_type=SlashCommandOptionType.ROLE,
                      required=True
                  )],
                  guild_ids=guilds_ids)
# @client.command()
async def server_init_moderator(ctx, role: discord.Role):
    await ctx.defer(hidden=True)

    if not ctx.author.id == ctx.guild.owner_id:
        await ctx.send(f"Command can only be used by owner of the server")
        return

    if mongodb_client.bot.guilds.count_documents({'guildID': ctx.guild.id, 'moderators': {'$in': [role.id]}}) > 0:
        mongodb_client.bot.guilds.find_one_and_update({'guildID': ctx.guild.id}, {'$pull': {'moderators': role.id}},
                                                      upsert=True)
        await ctx.send(f"Moderator <@&{role.id}> is unset")
    else:
        mongodb_client.bot.guilds.find_one_and_update({'guildID': ctx.guild.id}, {'$addToSet': {'moderators': role.id}},
                                                      upsert=True)
        await ctx.send(f"Moderator <@&{role.id}> is set")


@slash.subcommand(base='server',
                  subcommand_group='init',
                  name='administrator',
                  description="Add/delete administrator for bot",
                  options=[manage_commands.create_option(
                      name="role",
                      description="Role you want add to administrators",
                      option_type=SlashCommandOptionType.ROLE,
                      required=True
                  )],
                  guild_ids=guilds_ids)
# @client.command()
async def server_init_administrator(ctx, role: discord.Role):
    await ctx.defer(hidden=True)

    if not ctx.author.id == ctx.guild.owner_id:
        await ctx.send(f"Command can only be used by owner of the server")
        return

    if mongodb_client.bot.guilds.count_documents({'guildID': ctx.guild.id, 'administrators': {'$in': [role.id]}}) > 0:
        mongodb_client.bot.guilds.find_one_and_update({'guildID': ctx.guild.id}, {'$pull': {'administrators': role.id}},
                                                      upsert=True)
        await ctx.send(f"Administrator <@&{role.id}> is unset")
    else:
        mongodb_client.bot.guilds.find_one_and_update({'guildID': ctx.guild.id},
                                                      {'$addToSet': {'administrators': role.id}},
                                                      upsert=True)
        await ctx.send(f"Administrator <@&{role.id}> is set")


@slash.subcommand(base='server',
                  subcommand_group='init',
                  name='no_command_channel',
                  description="Add/delete channel to/from ignore command list",
                  options=[manage_commands.create_option(
                      name="channel",
                      description="Channel you want add to ignore list",
                      option_type=SlashCommandOptionType.CHANNEL,
                      required=True
                  )],
                  guild_ids=guilds_ids)
# @client.command()
async def server_init_no_command_channel(ctx, channel: discord.TextChannel):
    await ctx.defer(hidden=True)

    if not ctx.author.id == ctx.guild.owner_id:
        await ctx.send(f"Command can only be used by owner of the server")
        return

    if mongodb_client.bot.guilds.count_documents(
            {'guildID': ctx.guild.id, "no_command_channel_id's": {'$in': [channel.id]}}) > 0:
        mongodb_client.bot.guilds.find_one_and_update({'guildID': ctx.guild.id},
                                                      {'$pull': {"no_command_channel_id's": channel.id}},
                                                      upsert=True)
        await ctx.send(f"No command channel <#{channel.id}> is unset")
    else:
        mongodb_client.bot.guilds.find_one_and_update({'guildID': ctx.guild.id},
                                                      {'$addToSet': {"no_command_channel_id's": channel.id}},
                                                      upsert=True)
        await ctx.send(f"No command channel <#{channel.id}> is set")


@slash.subcommand(base='server',
                  subcommand_group='init',
                  name='system_channel',
                  description="Set/Unset system channel for the guild",
                  options=[manage_commands.create_option(
                      name="channel",
                      description="Channel you want to use as system",
                      option_type=SlashCommandOptionType.CHANNEL,
                      required=True
                  )],
                  guild_ids=guilds_ids)
# @client.command()
async def server_init_system_channel(ctx, channel: discord.TextChannel):
    await ctx.defer(hidden=True)

    if not ctx.author.id == ctx.guild.owner_id:
        await ctx.send(f"Command can only be used by owner of the server")
        return

    if mongodb_client.bot.guilds.count_documents(
            {'guildID': ctx.guild.id, "system_channel": {'$in': [channel.id]}}) > 0:
        mongodb_client.bot.guilds.find_one_and_update({'guildID': ctx.guild.id},
                                                      {'$unset': {"system_channel": channel.id}},
                                                      upsert=True)
        await ctx.send(f"System channel <#{channel.id}> is unset")
    else:
        mongodb_client.bot.guilds.find_one_and_update({'guildID': ctx.guild.id},
                                                      {'$set': {"system_channel": channel.id}},
                                                      upsert=True)
        await ctx.send(f"System channel <#{channel.id}> is set")


# BOT ------------------------------------------------------------------------------------------------------------------


@commands.is_owner()
@client.command()
async def bot_shutdown(ctx):
    await ctx.bot.logout()


# %PROBLEM%
"""
@commands.is_owner()
@client.command()
async def buptime(ctx):
    now_time = datetime.datetime.now().time().strftime('%c')
    total_time = relativedelta(datetime.datetime.strptime(now_time, '%c'), datetime.datetime.strptime(start_time, '%c'))

    await ctx.send(f"Bot uptime: "
                   f"{total_time.years} years:"
                   f"{total_time.leapdays} leap years:"
                   f"{total_time.months} months:"
                   f"{total_time.weeks} weeks:"
                   f"{total_time.days} days:"
                   f"{total_time.hours} hours:"
                   f"{total_time.minutes} minutes:"
                   f"{total_time.seconds} seconds:"
                   f"{total_time.microseconds} microseconds")
"""


@slash.subcommand(base='bot',
                  name='ping',
                  description="Show latency of the bot",
                  options=[],
                  guild_ids=guilds_ids)
# @client.command()
async def bot_ping(ctx):
    await ctx.defer(hidden=True)

    await ctx.send(f"🏓 Pong with {str(round(client.latency, 2))}")


@slash.subcommand(base='bot',
                  name='join',
                  description="Join bot to your voice channel",
                  options=[],
                  guild_ids=guilds_ids)
# @client.command()
async def bot_join(ctx):
    await ctx.defer(hidden=True)

    if ctx.guild.voice_client:
        voice_client = ctx.guild.voice_client

        if not voice_client.is_connected():
            await voice_client.connect(reconnect=False, timeout=10000)
        else:
            voice_channel = ctx.author.voice.channel

            if not voice_channel:
                return await ctx.send(f"Connect to voice channel to use this command")

            for member in voice_client.channel.members:
                if not member.bot:
                    return await ctx.send(f"Someone already using this bot")

            if voice_client.is_playing():
                voice_client.pause()
                await voice_client.move_to(channel=voice_channel)
            else:
                await voice_client.move_to(channel=voice_channel)

        return await ctx.send("Wassup homie?")
    else:
        try:
            voice_state = ctx.author.voice
            if voice_state:
                await voice_state.channel.connect(reconnect=False, timeout=10000)
            else:
                return await ctx.send(f"Connect to voice channel to use this command")

            return await ctx.send("Wassup homie?")
        except AttributeError:
            return await ctx.send(f"Some problems with player. Try again later")


@slash.subcommand(base='bot',
                  name='leave',
                  description="Leave bot from voice channel",
                  options=[],
                  guild_ids=guilds_ids)
# @client.command()
async def bot_leave(ctx):
    await ctx.defer(hidden=True)

    guild = ctx.guild

    if not ctx.author.id == guild.owner_id:
        await ctx.send(f"Command can only be used by owner of the server")
        return

    if guild.voice_client:
        voice_client = guild.voice_client
    else:
        return

    await voice_client.disconnect()

    try:
        await ctx.send('Thank you for kicking me out')
    except discord.NotFound:
        print('Channel does not exist')


@slash.subcommand(base='temporary',
                  subcommand_group='category',
                  name='lock',
                  description="Lock/unlock category",
                  options=[],
                  guild_ids=guilds_ids)
# @client.command()
async def temporary_category_lock(ctx):
    await ctx.defer()

    guild = ctx.guild
    category = ctx.channel.category

    if category:
        mongodb_guild = mongodb_client.bot.guilds.find_one(
            {'guildID': guild.id, 'temporary.categories.category_id': category.id},
            {'temporary.categories': 1, '_id': 0})

        # print(mongodb_guild)
        if mongodb_guild:
            categories = list(
                filter(lambda c: c['category_id'] == category.id, mongodb_guild['temporary']['categories']))

            owner_id = categories[0]['owner_id']

            if owner_id == ctx.author.id:
                overwrites = category.overwrites_for(guild.default_role)

                if not overwrites.view_channel:
                    overwrites.view_channel = True
                    await ctx.send('Category unlocked')
                else:
                    overwrites.view_channel = False
                    await ctx.send('Category locked')

                await category.set_permissions(guild.default_role, overwrite=overwrites, reason='Lock')

            else:
                await ctx.send('You are not category owner')


@slash.subcommand(base='temporary',
                  subcommand_group='category',
                  name='invite_role',
                  description="Invite/delete member to/from temporary category",
                  options=[manage_commands.create_option(
                      name="role",
                      description="Role you want to invite/delete",
                      option_type=SlashCommandOptionType.ROLE,
                      required=True
                  )],
                  guild_ids=guilds_ids)
# @client.command()
async def temporary_category_invite_role(ctx, role):
    await ctx.defer()

    guild = ctx.guild
    category = ctx.channel.category

    if category:
        mongodb_guild = mongodb_client.bot.guilds.find_one({'guildID': guild.id,
                                                            'temporary.categories.category_id': category.id
                                                            },
                                                           {'temporary.categories': 1, '_id': 0})

        if mongodb_guild:
            categories = list(
                filter(lambda c: c['category_id'] == category.id, mongodb_guild['temporary']['categories']))

            owner_id = categories[0]['owner_id']
            if owner_id == ctx.author.id:
                overwrites = category.overwrites_for(role)

                if overwrites.view_channel:
                    overwrites = None
                    await ctx.send(f'<@&{role.id}> kicked from category')
                else:
                    overwrites.view_channel = True
                    await ctx.send(f'<@&{role.id}> invited to category')

                await category.set_permissions(role, overwrite=overwrites, reason='Invite')

            else:
                await ctx.send('You are not category owner')


@slash.subcommand(base='temporary',
                  subcommand_group='category',
                  name='disc_member',
                  description="Disconnect member from temporary category voice channel",
                  options=[manage_commands.create_option(
                      name="member",
                      description="Member you want to disconnect",
                      option_type=SlashCommandOptionType.USER,
                      required=True
                  )],
                  guild_ids=guilds_ids)
# @client.command()
async def temporary_category_disc_member(ctx, member):
    await ctx.defer()

    guild = ctx.guild
    category = ctx.channel.category

    if category:
        mongodb_guild = mongodb_client.bot.guilds.find_one({'guildID': guild.id,
                                                            'temporary.categories.category_id': category.id
                                                            },
                                                           {'temporary.categories': 1, '_id': 0})

        if mongodb_guild:
            categories = list(
                filter(lambda c: c['category_id'] == category.id, mongodb_guild['temporary']['categories']))

            owner_id = categories[0]['owner_id']
            if owner_id == ctx.author.id:

                member_voice = member.voice

                if member_voice:
                    if member_voice.channel.category == category:
                        await member.edit(voice_channel=None)
                        await ctx.send(f'<@{member.id}> disconnected from category')
            else:
                await ctx.send('You are not category owner')


@slash.subcommand(base='temporary',
                  subcommand_group='category',
                  name='invite_member',
                  description="Invite/delete member to/from temporary category",
                  options=[manage_commands.create_option(
                      name="member",
                      description="Member you want to invite/delete",
                      option_type=SlashCommandOptionType.USER,
                      required=True
                  )],
                  guild_ids=guilds_ids)
# @client.command()
async def temporary_category_invite_member(ctx, member):
    await ctx.defer()

    guild = ctx.guild
    category = ctx.channel.category

    if category:
        mongodb_guild = mongodb_client.bot.guilds.find_one({'guildID': guild.id,
                                                            'temporary.categories.category_id': category.id
                                                            },
                                                           {'temporary.categories': 1, '_id': 0})

        if mongodb_guild:
            categories = list(
                filter(lambda c: c['category_id'] == category.id, mongodb_guild['temporary']['categories']))

            owner_id = categories[0]['owner_id']
            if owner_id == ctx.author.id:
                overwrites = category.overwrites_for(member)

                if overwrites.view_channel:
                    overwrites = None
                    await ctx.send(f'<@{member.id}> kicked from category')

                    # member_voice = member.voice

                    # if member_voice:
                    #    if member_voice.channel.category == category:
                    #        await member.edit(voice_channel=None)
                else:
                    overwrites.view_channel = True
                    await ctx.send(f'<@{member.id}> invited to category')

                await category.set_permissions(member, overwrite=overwrites, reason='Invite')

            else:
                await ctx.send('You are not category owner')


@slash.subcommand(base='temporary',
                  subcommand_group='category',
                  name='rename',
                  description="Rename temporary category",
                  options=[manage_commands.create_option(
                      name="text",
                      description="Name of category",
                      option_type=SlashCommandOptionType.STRING,
                      required=True
                  )],
                  guild_ids=guilds_ids)
# @client.command()
async def temporary_category_rename(ctx, text):
    await ctx.defer()

    guild = ctx.guild
    category = ctx.channel.category

    if category:
        mongodb_guild = mongodb_client.bot.guilds.find_one({'guildID': guild.id,
                                                            'temporary.categories.category_id': category.id
                                                            },
                                                           {'temporary.categories': 1, '_id': 0})

        if mongodb_guild:
            categories = list(
                filter(lambda c: c['category_id'] == category.id, mongodb_guild['temporary']['categories']))

            owner_id = categories[0]['owner_id']

            if owner_id == ctx.author.id:
                for text_channel in category.text_channels:
                    await text_channel.edit(name=f'text-{text}')
                for voice_channel in category.voice_channels:
                    await voice_channel.edit(name=f'voice-{text}')

                await category.edit(name=f'category-{text}')
                await ctx.send(f'{category.mention} renamed to {text}')
            else:
                await ctx.send('You are not category owner')


@slash.subcommand(base='temporary',
                  subcommand_group='category',
                  name='init',
                  description="Set/unset voice channel as init for temporary categories",
                  options=[manage_commands.create_option(
                      name="voice_channel",
                      description="Voice channel you want to set/unset",
                      option_type=SlashCommandOptionType.CHANNEL,
                      required=False
                  )],
                  guild_ids=guilds_ids)
# @client.command()
async def temporary_category_init(ctx, voice_channel=None):
    await ctx.defer()

    guild = ctx.guild
    if not ctx.author.id == guild.owner_id:
        await ctx.send(f"Command can only be used by owner of the server")
        return

    if voice_channel is None:
        category = ctx.channel.category

        if category:
            voice_channel = await category.create_voice_channel('JOIN to CREATE category')
        else:
            voice_channel = await guild.create_voice_channel('JOIN to CREATE category')

    if mongodb_client.bot.guilds.count_documents({'guildID': guild.id,
                                                  'temporary.category_init':
                                                      {'$in': [voice_channel.id]}
                                                  }) > 0:
        mongodb_client.bot.guilds.find_one_and_update({'guildID': guild.id},
                                                      {'$pull':
                                                           {'temporary.category_init': voice_channel.id}
                                                       },
                                                      upsert=True)
        await ctx.send(f"Channel <#{voice_channel.id}> is unset")
    else:
        mongodb_client.bot.guilds.find_one_and_update({'guildID': guild.id},
                                                      {'$addToSet':
                                                           {'temporary.category_init': voice_channel.id}
                                                       },
                                                      upsert=True)
        await ctx.send(f"Channel <#{voice_channel.id}> is set")


@slash.subcommand(base='temporary',
                  subcommand_group='category',
                  name='owner',
                  description="Get/set owner of the category",
                  options=[manage_commands.create_option(
                      name="new_owner",
                      description="New owner of the category",
                      option_type=SlashCommandOptionType.USER,
                      required=False
                  )],
                  guild_ids=guilds_ids)
# @client.command()
async def temporary_category_owner(ctx, new_owner=None):
    await ctx.defer()

    guild = ctx.guild
    category = ctx.channel.category
    mongodb_guilds = mongodb_client.bot.guilds

    categories = mongodb_guilds.find_one(
        {'guildID': guild.id, 'temporary.categories.category_id': category.id},
        {'temporary.categories': 1, '_id': 0})

    if categories:
        categories = list(filter(lambda c: c['category_id'] == category.id, categories['temporary']['categories']))

        if categories:
            # member = get(guild.members, id=categories[0]['owner_id'])
            # if member.nick:

            member = ctx.author
            owner = categories[0]['owner_id']

            if new_owner is not None:
                if owner == member.id:
                    default_role = discord.PermissionOverwrite(view_channel=True,
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
                                                               move_members=False)

                    await category.set_permissions(new_owner, overwrite=default_role)

                    await ctx.send(f'<@{member.id}> was owner but give it away :(\nNew owner is <@{new_owner.id}> :)')

                    mongodb_guilds.find_one_and_update({'guildID': guild.id,
                                                        'temporary.categories.owner_id': member.id},
                                                       {'$set':
                                                            {'temporary.categories.$.owner_id': new_owner.id}
                                                        })
            else:
                await ctx.send(f"Owner of the {category.mention} is <@{owner}>")
    else:
        await ctx.send('It is not temporary category')


"""
# %TEMP%
@slash.subcommand(base='text',
                  name='create',
                  description="Creating personal text channel",
                  options=[])
                  #guild_ids=test_guild)
@client.command()
async def _text_create(ctx):
    #await ctx.respond()

    guild = ctx.guild
    member = ctx.author
    # admin_role = get(guild.roles, name="ADMINistrator")

    mongodb_guild = mongodb_client.bot.guilds.find_one({'guildID': guild.id},
                                                       {'moderators': 1, 'administrators': 1, '_id': 0})

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True,
                                              manage_channels=True,
                                              manage_permissions=True,
                                              create_instant_invite=True,
                                              connect=True,
                                              speak=True,
                                              stream=True,
                                              use_voice_activation=True,
                                              priority_speaker=True,
                                              mute_members=True,
                                              deafen_members=True,
                                              move_members=True),
        # admin_role: discord.PermissionOverwrite(read_messages=True),
        member: discord.PermissionOverwrite(read_messages=True)
    }
    moderators = mongodb_guild.get('moderators')
    administrators = mongodb_guild.get('administrators')

    if moderators:
        for moderator in moderators:
            overwrites[get(guild.roles, id=moderator)] = discord.PermissionOverwrite(read_messages=True)
    if administrators:
        for administrator in administrators:
            overwrites[get(guild.roles, id=administrator)] = discord.PermissionOverwrite(read_messages=True)

    category = get(guild.categories, id=787680047010938911)

    text_channel = await guild.create_text_channel(f"t-{member.name}",
                                                   overwrites=overwrites,
                                                   category=category)
"""

# RUN ------------------------------------------------------------------------------------------------------------------


token = os.getenv('token')
if token:
    client.run(token)


# serverStatusResult=mongodb_client.command("serverStatus")
# print(serverStatusResult)
# print(mongodb_client.server_info())
# print(mongodb_client.bot.serverStatus().connections)


# ----------------------------------------------------------------------------------------------------------------------