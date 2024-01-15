# import asyncio
import os
import discord.ext.commands
import discord.utils
import pymongo
import pytz
import utils
import random

from datetime import datetime, timedelta
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
    # OTHER -----------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    async def _roll_role(self, member: discord.Member, guild: discord.Guild, name='', rate=3):
        if rate == 0 or round(random.random(), rate) == 1.0 / (10 ** rate):
            if not discord.utils.get(member.roles, name=name):
                role = discord.utils.get(guild.roles, name=name)

                if not role:
                    role = await guild.create_role(name=name, color=discord.Color.fuchsia(),
                                                   hoist=True)
                await member.add_roles(role)
                await member.send(f'Поздравляю. Ты разблокировал(а) секретную роль: {role.name}')

    # ------------------------------------------------------------------------------------------------------------------
    # EVENTS -----------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    async def _on_event(self, event='', guild=None, *args):
        if not guild.system_channel:
            return
        else:
            system_channel = guild.system_channel

        event_embed = discord.Embed()
        event_embed.timestamp = datetime.now(tz=pytz.timezone('Europe/Kiev'))

        if event == 'on_voice_state_update':
            event_embed.title = 'Voice'

            member = args[0]
            before = args[1]
            after = args[2]

            member: discord.Member
            before: discord.VoiceState
            after: discord.VoiceState

            if after.channel and before.channel:
                if after.channel != before.channel:
                    event_embed.color = discord.Color.blurple()
                    event_embed.description = f"**📨\n{member.mention} переместился в {after.channel.type} `{after.channel.name}`**"

                    return await system_channel.send(embed=event_embed)
            elif after.channel is None and before.channel:
                event_embed.color = discord.Color.brand_red()
                event_embed.description = f"**📤\n{member.mention} покинул {before.channel.type} `{before.channel.name}`**"

                return await system_channel.send(embed=event_embed)

            if after.channel:
                if after.channel != before.channel:
                    event_embed.color = discord.Color.brand_green()
                    event_embed.description = f"**📥\n{member.mention} подключился к {after.channel.type} `{after.channel.name}`**"

                    return await system_channel.send(embed=event_embed)

            return

        if event == 'on_guild_channel_create':
            event_embed.title = 'Channel'
            event_embed.color = discord.Color.brand_green()

            channel = args[0]
            channel: discord.abc.GuildChannel

            event_embed.description = f"**✔️\nСоздан {channel.type} `{channel.name}`**"

            await system_channel.send(embed=event_embed)

            return

        if event == 'on_guild_channel_delete':
            event_embed.title = 'Channel'
            event_embed.color = discord.Color.brand_red()

            channel = args[0]
            channel: discord.abc.GuildChannel

            event_embed.description = f"**✖️\nУдален {channel.type} `{channel.name}`**"

            await system_channel.send(embed=event_embed)

            return

        if event == 'on_guild_channel_update':
            event_embed.title = 'Channel'
            event_embed.color = discord.Color.gold()

            before = args[0]
            after = args[1]

            before: discord.abc.GuildChannel
            after: discord.abc.GuildChannel

            changes = ''
            for attr in [attr for attr in dir(after) if not attr.startswith('_')]:
                value = getattr(after, attr)
                value_changed = getattr(before, attr)

                if callable(value):
                    continue

                if value != value_changed:
                    changes = f'{changes}\n {attr}'

            if  not changes:
                return

            if after.name != before.name:
                event_embed.description = f'**🚧\nОбновлен {after.type} `{before.name}` -> `{after.name}`**\n{changes}'
            else:
                event_embed.description = f'**🚧\nОбновлен {after.type} `{before.name}`**\n{changes}'

            await system_channel.send(embed=event_embed)

            return

        if event == 'on_member_join':
            event_embed.title = 'Guild'
            event_embed.color = discord.Color.brand_green()

            member = args[0]
            member: discord.Member

            event_embed.description = f'**💦\n{member.mention} присоединился к серверу**'

            await system_channel.send(embed=event_embed)

            return

        if event == 'on_member_remove':
            event_embed.title = 'Guild'
            event_embed.color = discord.Color.brand_red()

            member = args[0]
            member: discord.Member

            event_embed.description = f'**💧\n{member.mention} покинул сервер**'

            await system_channel.send(embed=event_embed)

            return

        # if event == 'on_user_update':
        #     event_embed.title = 'User'
        #     event_embed.color = discord.Color.gold()
        #
        #     before = args[0]
        #     after = args[1]
        #
        #     before: discord.User
        #     after: discord.User
        #
        #     if before.avatar != after.avatar:
        #         event_embed.description = f'🚧\n{after.mention} обновил [аватар]({after.avatar})'
        #         event_embed.set_thumbnail(url=after.avatar)
        #
        #         await system_channel.send(embed=event_embed)
        #
        #     if before.global_name != after.global_name:
        #         event_embed.description = f'🚧\n{after.mention} обновил юзернейм `{before.global_name}` -> `{after.global_name}`'
        #
        #         await system_channel.send(embed=event_embed)
        #
        #     return

        if event == 'on_member_update':
            event_embed.title = 'Member'
            event_embed.color = discord.Color.gold()

            before = args[0]
            after = args[1]

            before: discord.Member
            after: discord.Member

            if before.nick != after.nick:
                event_embed.description = f'**🚧\n{after.mention} обновил никнейм `{before.nick}` -> `{after.nick}`**'

                await system_channel.send(embed=event_embed)

            if before.roles != after.roles:
                role_added = [role for role in after.roles if role not in before.roles]
                role_deleted = []

                if not role_added:
                    role_deleted = [role for role in before.roles if role not in after.roles]

                if role_added:
                    event_embed.color = discord.Color.brand_green()
                    event_embed.description = f'**➕\n{after.mention} получил роль `{role_added.pop().name}`**'

                    await system_channel.send(embed=event_embed)
                elif role_deleted:
                    event_embed.color = discord.Color.brand_red()
                    event_embed.description = f'**➖\n{after.mention} потерял роль `{role_deleted.pop().name}`**'

                    await system_channel.send(embed=event_embed)

            if before.avatar != after.avatar:
                event_embed.description = f'**🚧\n{after.mention} обновил [аватар]({after.avatar})**'
                event_embed.set_thumbnail(url=after.avatar)

                await system_channel.send(embed=event_embed)

            return

        if event == 'on_guild_update':
            event_embed.title = 'Guild'
            event_embed.color = discord.Color.gold()

            before = args[0]
            after = args[1]

            before: discord.Guild
            after: discord.Guild

            changes = ''
            for attr in [attr for attr in dir(after) if not attr.startswith('_')]:
                value = getattr(after, attr)
                value_changed = getattr(before, attr)

                if callable(value):
                    continue

                if isinstance(value, discord.utils.SequenceProxy):
                    value = list(value)
                    value_changed = list(value_changed)

                if value != value_changed:
                    changes = f'{changes}\n {attr}'

            if not changes:
                return

            if after.name != before.name:
                event_embed.description = f'**🚧\nОбновлена информация сервера `{before.name}` -> `{after.name}`**\n{changes}'
            else:
                event_embed.description = f'**🚧\nОбновлена информация сервера `{before.name}`**\n{changes}'

            await system_channel.send(embed=event_embed)

            return

        if event == 'on_guild_role_create':
            event_embed.title = 'Role'
            event_embed.color = discord.Color.brand_green()

            role = args[0]
            role: discord.Role

            event_embed.description = f'**✔️\nСоздана роль `{role.name}`**'

            await system_channel.send(embed=event_embed)

            return

        if event == 'on_guild_role_delete':
            event_embed.title = 'Role'
            event_embed.color = discord.Color.brand_red()

            role = args[0]
            role: discord.Role

            event_embed.description = f'**✖️\nУдалена роль `{role.name}`**'

            await system_channel.send(embed=event_embed)

            return

        if event == 'on_guild_role_update':
            event_embed.title = 'Role'
            event_embed.color = discord.Color.gold()

            before = args[0]
            after = args[1]

            before: discord.Role
            after: discord.Role

            changes = ''
            for attr in [attr for attr in dir(after) if not attr.startswith('_')]:
                value = getattr(after, attr)
                value_changed = getattr(before, attr)

                if callable(value):
                    continue

                if value != value_changed:
                    changes = f'{changes}\n {attr}'

            if not changes:
                return

            if after.name != before.name:
                event_embed.description = f'**🚧\nОбновлена роль `{before.name}` -> `{after.name}`**\n{changes}'
            else:
                event_embed.description = f'**🚧\nОбновлена роль `{before.name}`**\n{changes}'

            await system_channel.send(embed=event_embed)

            return

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        await self._on_event('on_voice_state_update', member.guild, member, before, after)
        # if member == client.user:
        #    return

        # if member.bot:
        #    return

        if not before.self_deaf == after.self_deaf:
            # print('self deaf')
            pass

        if not before.self_mute == after.self_mute:
            # print('self mute')
            pass

        if not before.self_video == after.self_video:
            # print('video')
            if after.self_video:
                guild = member.guild

                if not guild:
                    return

                await self._roll_role(member=member, guild=guild, name='🔞Порнозвезда', rate=3)

        if not before.self_stream == after.self_stream:
            # print('stream')

            if after.self_stream:
                guild = member.guild

                if not guild:
                    return

                await self._roll_role(member=member, guild=guild, name='🎬Режиссер', rate=3)

        if not before.deaf == after.deaf:
            # print('deaf')
            pass

        if not before.mute == after.mute:
            # print('mute')
            pass

        if before.channel:
            if after.channel:
                if before.channel == after.channel:
                    return

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
                    await self._roll_role(member=member, guild=guild, name='♋Живая легенда', rate=0)

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

        if after.channel is not None:
            if before.channel:
                if before.channel == after.channel:
                    return

            # User join voice channel

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

                try:
                    await member.move_to(channel=voice_channel)
                except discord.HTTPException:
                    if len(voice_channel.members) == 0:
                        await voice_channel.delete()

                await voice_channel.set_permissions(member, overwrite=utils.default_role)

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
                last_message_seconds = (datetime.now(tz=pytz.utc).replace(tzinfo=None) - datetime.strptime(last_message,
                                                                                                           '%Y-%m-%d %H:%M:%S')).total_seconds()

            messages_count = 1
            messages_count += cache.stats.get(guild.id, {}).get('members', {}).get(author.id, {}).get('messages_count',
                                                                                                      0)

            cache.stats[guild.id]['members'][author.id]['messages_count'] = messages_count
            message_xp_delay = cache.stats.get(guild.id, {}).get('xp', {}).get('message_xp_delay', 60)

            # Count messages only every 60 seconds
            if not last_message_seconds or last_message_seconds > message_xp_delay:
                date = datetime.now(tz=pytz.utc)
                date = date.strftime('%Y-%m-%d %H:%M:%S')

                messages_count_xp = 1
                messages_count_xp += cache.stats.get(guild.id, {}).get('members', {}).get(author.id, {}).get(
                    'messages_count_xp', 0)

                cache.stats[guild.id]['members'][author.id]['messages_count_xp'] = messages_count_xp
                cache.stats[guild.id]['members'][author.id]['last_message'] = date

            # Unique roles

            # Lucky message (1 in 100.000)
            await self._roll_role(member=author, guild=guild, name='🍀Лакер', rate=5)

            # Toxic words (1 in 1.000)
            if any(word.lower() in bad_words for word in message.content.split(' ')):
                await self._roll_role(member=author, guild=guild, name='🤢Токсик', rate=3)

            # . in the end of sentence (1 in 1.000)
            if message.content.endswith('.'):
                await self._roll_role(member=author, guild=guild, name='🤓Душнила', rate=3)

            # 'пам' in sentence (1 in 1.000)
            if 'пам' in message.content.lower():
                await self._roll_role(member=author, guild=guild, name='💢Пам', rate=3)

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

    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        await self._on_event('on_guild_channel_create', channel.guild, channel)

    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        await self._on_event('on_guild_channel_delete', channel.guild, channel)

    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        await self._on_event('on_guild_channel_update', after.guild, before, after)

    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        await self._on_event('on_guild_update', after, before, after)

    async def on_member_join(self, member: discord.Member):
        await self._on_event('on_member_join', member.guild, member)

    async def on_member_remove(self, member: discord.Member):
        await self._on_event('on_member_remove', member.guild, member)

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        await self._on_event('on_member_update', after.guild, before, after)

    # async def on_user_update(self, before: discord.User, after: discord.User):
    #     await self._on_event('on_user_update', before, after)

    async def on_guild_role_create(self, role: discord.Role):
        await self._on_event('on_guild_role_create', role.guild, role)

    async def on_guild_role_delete(self, role: discord.Role):
        await self._on_event('on_guild_role_delete', role.guild, role)

    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        await self._on_event('on_guild_role_update', after.guild, before, after)

    # async def on_scheduled_event_create(self, event: discord.ScheduledEvent):
    #     await self._on_event('on_scheduled_event_create', event)

    # async def on_scheduled_event_delete(self, event: discord.ScheduledEvent):
    #     await self._on_event('on_scheduled_event_delete', event)

    # async def on_scheduled_event_create(self, before: discord.ScheduledEvent, after: discord.ScheduledEvent):
    #     await self._on_event('on_scheduled_event_update', before, after)

    # async def on_stage_instance_create(self, stage_instance: discord.StageInstance):
    #     await self._on_event('on_stage_instance_create', stage_instance)

    # async def on_stage_instance_delete(self, stage_instance: discord.StageInstance):
    #     await self._on_event('on_stage_instance_delete', stage_instance)

    # async def on_stage_instance_update(self, before: discord.StageInstance, after: discord.StageInstance):
    #     await self._on_event('on_stage_instance_update', before, after)

    # async def on_thread_create(self, thread: discord.Thread):
    #     await self._on_event('on_thread_create', thread)

    # async def on_thread_remove(self, thread: discord.Thread):
    #     await self._on_event('on_thread_remove', thread)

    # async def on_thread_update(self, before: discord.Thread, after: discord.Thread):
    #     await self._on_event('on_thread_update', before, after)

    # async def on_thread_member_join(self, member: discord.Member):
    #     await self._on_event('on_thread_member_join', member)

    # async def on_thread_member_remove(self, member: discord.Member):
    #     await self._on_event('on_thread_member_remove', member)
