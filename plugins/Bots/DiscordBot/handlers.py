# import asyncio
import os
import discord.ext.commands
import discord.utils
import pymongo
import pytz
import utils
import random

from datetime import datetime
from plugins.DataBase.mongo import MongoDataBase
from version import __version__
from utils import *
from utils import cache

bad_words = (
    'ебал',
    'пидар',
    'хуй',
    'пиздец',
    'блять',
    'пизда',
    'залупа',
    'гандон',
    'еблан',
    'ублюдок',
    'сука',
    'долбаеб',
    'блядина',
    'шлюха',
    'анус',
    'ебу',
    'ебать',
    'хуйня',
    'проебали',
    'похуй',
    'проебал',
    'нахуй',
    'пздц',
    'ахуеть',
    'пиздос',
    'хуита',
    'ебани',
    'ебни',
    'ёбни',
    'ёбаный',
    'ебануться',
    'пиздюк',
    'уебище',
    'уёбище',
    'блядина',
    'пидарас',
    'уебан',
)


class DiscordBotHandler:
    """
    DiscordBot Handler
    """

    def __init__(self, webSerber, discordBot, mongoDataBase: MongoDataBase):
        self.webServer = webSerber
        self.discordBot = discordBot
        self.mongoDataBase = mongoDataBase

        # register handlers
        for handler in [handler for handler in dir(DiscordBotHandler) if not handler.startswith('_')]:
            callback = getattr(self, handler)
            self.discordBot.client.event(callback)

    # ------------------------------------------------------------------------------------------------------------------
    # EVENTS -----------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
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
            if after.self_video:
                guild = member.guild

                if not guild:
                    return

                # 1 in 1.000 when start video
                if round(random.random(), 3) == 0.001:
                    if not discord.utils.get(member.roles, name='🔞Порнозвезда'):
                        role = discord.utils.get(guild.roles, name='🔞Порнозвезда')

                        if not role:
                            role = await guild.create_role(name='🔞Порнозвезда', color=discord.Color.fuchsia(),
                                                           hoist=True)
                        await member.add_roles(role)
                        await member.send(f'Поздравляю. Ты разблокировал(а) секретную роль: {role.name}')

            return

        if not before.self_stream == after.self_stream:
            # print('stream')

            if after.self_stream:
                guild = member.guild

                if not guild:
                    return
                # 1 in 1.000 when start stream
                if round(random.random(), 3) == 0.001:
                    if not discord.utils.get(member.roles, name='🎬Режиссер'):
                        role = discord.utils.get(guild.roles, name='🎬Режиссер')

                        if not role:
                            role = await guild.create_role(name='🎬Режиссер', color=discord.Color.orange(),
                                                           hoist=True)
                        await member.add_roles(role)
                        await member.send(f'Поздравляю. Ты разблокировал(а) секретную роль: {role.name}')
            return

        if not before.deaf == after.deaf:
            # print('deaf')
            return

        if not before.mute == after.mute:
            # print('mute')
            return

        if before.channel:
            # User moved or leaves voice channel
            voice_channel = before.channel
            members = voice_channel.members
            guild = voice_channel.guild

            voice_channel_cache = cache.stats.get(guild.id, {}).get('tvoice_channels', {}).get(voice_channel.id, {})
            member_cache = cache.stats.get(guild.id, {}).get('members', {}).get(member.id, {})

            member_joined = member_cache.get('joined', '')

            if member_joined:
                voicetime = (datetime.now(tz=pytz.utc).replace(tzinfo=None) - datetime.strptime(member_joined,
                                                                                                '%Y-%m-%d %H:%M:%S')).total_seconds()

                # was in voice 69 hours (248400 seconds) or more
                if voicetime >= 248400:
                    if not discord.utils.get(member.roles, name='♋Живая легенда'):
                        role = discord.utils.get(guild.roles, name='♋Живая легенда')

                        if not role:
                            role = await guild.create_role(name='♋Живая легенда', color=discord.Color.purple(),
                                                           hoist=True)
                        await member.add_roles(role)
                        await member.send(f'Поздравляю. Ты разблокировал(а) секретную роль: {role.name}')

                voicetime += member_cache.get('voicetime', 0)

                cache.stats[guild.id]['members'][member.id]['voicetime'] = voicetime
                del cache.stats[guild.id]['members'][member.id]['joined']

            if voice_channel_cache:
                if len(members) == 0:
                    # Leaves last member in voice channel
                    await voice_channel.delete()

                    del cache.stats[guild.id]['tvoice_channels'][voice_channel.id]
                else:
                    if member.bot:
                        return

                    # Leaves not last member in voice channel
                    owner = voice_channel_cache.get('owner', {})

                    if owner.get('id', '') == member.id:
                        # Leaves owner of voice channel
                        new_owner = None

                        for tmember in members:
                            if not tmember.bot:
                                new_owner = tmember

                        if new_owner:
                            await voice_channel.set_permissions(new_owner, overwrite=utils.default_role)
                            await voice_channel.edit(name=f'@{new_owner.name}')

                            cache.stats[guild.id]['tvoice_channels'][voice_channel.id]['owner']['id'] = new_owner.id

        # User join voice channel
        if after.channel is not None:
            voice_channel = after.channel
            guild = voice_channel.guild

            guild_cache = self.discordBot.guilds.get(guild.id, {})
            if not guild_cache:
                return

            init_channel = guild_cache.get('temporary', {}).get('inits', {}).get(f'{voice_channel.id}', '')

            if init_channel:
                category = voice_channel.category

                if category:
                    voice_channel = await category.create_voice_channel(name=f'@{member.name}',
                                                                        position=voice_channel.position + 1)
                else:
                    voice_channel = await guild.create_voice_channel(name=f'@{member.name}',
                                                                     position=voice_channel.position + 1)

                cache.stats[guild.id]['tvoice_channels'][voice_channel.id]['owner']['id'] = member.id

                await voice_channel.set_permissions(member, overwrite=utils.default_role)
                await member.move_to(channel=voice_channel)

                # self.discordBot.guilds[guild.id]['temporary']['channels'][f'{voice_channel.id}']= {'owner': {'id': member.id}}
            else:
                # Joined not in init channel
                date = datetime.now(tz=pytz.utc)
                date = date.strftime('%Y-%m-%d %H:%M:%S')

                cache.stats[guild.id]['members'][member.id]['joined'] = date

                # query = {f'members.{member.id}.stats.joined': date}
                # filter = {'id': guild.id}
                #
                # mongoUpdate = self.mongoDataBase.update_field(database_name='dbot', collection_name='guilds',
                #                                               action='$set',
                #                                               query=query, filter=filter)
                #
                # if mongoUpdate is None:
                #     print('Not updated joined value of member in DataBase')
                # else:
                #     self.discordBot.guilds[guild.id] = mongoUpdate
                    # self.discordBot.guilds[guild.id]['members'][f'{member.id}']['stats']['joined'] = date

    # async def on_guild_join(self, guild: discord.Guild):
    #     query = {f'guilds.id': guild.id}
    #     filter = {'id': guild.id}
    #
    #     if self.mongoDataBase.update_field(database_name='dbot', collection_name='guilds', action='$set', query=query,
    #                                        filter=filter) is None:
    #         print('Guild not added to DataBase')

    async def on_ready(self):
        if not os.getenv('DEBUG', '0').lower() in ['true', 't', '1']:
            guild = None
        else:
            try:
                guild = self.discordBot.client.get_guild(int(os.getenv('TEST_GUILD_ID', '')))
            except Exception:
                guild = None

        await self.discordBot.set_default_commands(guild=guild)
        # await self.discordBot.clear_default_commands(guild=guild)

        status = discord.Status.online
        updated = datetime.now(tz=pytz.timezone('Europe/Kiev')).strftime('%H:%M:%S | %d/%m/%y')
        activity = discord.Game(name=f"v{__version__} | {updated}")

        await self.discordBot.client.change_presence(status=status, activity=activity)

    async def on_message(self, message: discord.Message):
        try:
            if not message.guild:
                return

            if message.author.bot:
                return

            guild = message.guild
            author = message.author

            # query = {f'members.{author.id}.stats.messages_count': 1}
            # filter = {'id': message.guild.id}
            #
            # with pymongo.timeout(0.3):
            #     mongoUpdate = self.mongoDataBase.update_field(database_name='dbot', collection_name='guilds', action='$inc',
            #                                                   filter=filter,
            #                                                   query=query)
            # if mongoUpdate is None:
            #     print('Not updated messages count of member in DataBase')
            # else:
            #     self.discordBot.guilds[message.guild.id] = mongoUpdate
            last_message = cache.stats[guild.id]['members'][author.id]['last_message']
            last_message_seconds = None
            if last_message:
                last_message_seconds = (datetime.now(tz=pytz.utc).replace(tzinfo=None) - datetime.strptime(last_message, '%Y-%m-%d %H:%M:%S')).total_seconds()

            messages_count = 1
            messages_count += cache.stats.get(guild.id, {}).get('members', {}).get(author.id, {}).get('messages_count', 0)

            cache.stats[guild.id]['members'][author.id]['messages_count'] = messages_count
            message_xp_delay = cache.stats.get(guild.id, {}).get('xp', {}).get('message_xp_delay', 60)

            # Count messages only every 60 seconds
            if not last_message_seconds or last_message_seconds > message_xp_delay:
                date = datetime.now(tz=pytz.utc)
                date = date.strftime('%Y-%m-%d %H:%M:%S')

                messages_count_xp = 1
                messages_count_xp += cache.stats.get(guild.id, {}).get('members', {}).get(author.id, {}).get('messages_count_xp', 0)

                cache.stats[guild.id]['members'][author.id]['messages_count_xp'] = messages_count_xp
                cache.stats[guild.id]['members'][author.id]['last_message'] = date

            # Unique roles
            # Lucky message (1 in 100.000)
            if round(random.random(), 5) == 0.00001:
                if not discord.utils.get(author.roles, name='🍀Лакер'):
                    role = discord.utils.get(message.guild.roles, name='🍀Лакер')

                    if not role:
                        role = await message.guild.create_role(name='🍀Лакер', color=discord.Color.green(),
                                                               hoist=True)

                    await message.guild.get_member(author.id).add_roles(role)
                    await author.send(f'Поздравляю. Ты разблокировал(а) секретную роль: {role.name}')

            # Toxic words (1 in 1.000)
            if any(word.lower() in bad_words for word in message.content.split(' ')):
                if round(random.random(), 3) == 0.001:
                    role = discord.utils.get(message.guild.roles, name='🤢Токсик')

                    if not role:
                        role = await message.guild.create_role(name='🤢Токсик', color=discord.Color.brand_green(),
                                                               hoist=True)

                    await message.guild.get_member(author.id).add_roles(role)
                    await author.send(f'Поздравляю. Ты разблокировал(а) секретную роль: {role.name}')

            # . in the end of sentence (1 in 1.000)
            if message.content.endswith('.'):
                if round(random.random(), 3) == 0.001:
                    role = discord.utils.get(message.guild.roles, name='🤓Душнила')

                    if not role:
                        role = await message.guild.create_role(name='🤓Душнила', color=discord.Color.dark_red(),
                                                               hoist=True)

                    await message.guild.get_member(author.id).add_roles(role)
                    await author.send(f'Поздравляю. Ты разблокировал(а) секретную роль: {role.name}')

            # 'пам' in sentence (1 in 1.000)
            if 'пам' in message.content.lower():
                if round(random.random(), 3) == 0.001:
                    role = discord.utils.get(message.guild.roles, name='💢Пам')

                    if not role:
                        role = await message.guild.create_role(name='💢Пам', color=discord.Color.dark_magenta(),
                                                               hoist=True)

                    await message.guild.get_member(author.id).add_roles(role)
                    await author.send(f'Поздравляю. Ты разблокировал(а) секретную роль: {role.name}')

        except Exception as e:
            print(e)

    # async def on_error(event, *args, **kwargs):
    # args
    # {
    #     "message": "A message saying you are being rate limited",
    #     "retry_after": "The number of seconds to wait before submitting another request",
    #     "global": "A value indicating if you are being globally rate limited or not",
    #     "code?": "An error code for some limits",
    # }

    # if type(args[1]) == type(int):
    #     return await asyncio.sleep(args[1])
    # print(event, args, kwargs)
