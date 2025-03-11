import logging
from typing import Union, Optional
import discord.ext.commands
import discord.utils
import pytz

from datetime import datetime
from version import __version__
from utils import *
from utils import cache
from plugins.Bots.DiscordBot.roles import secret_roles

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

    async def _on_event_send_embed(self, event='', guild=None, *args):
        """
        Send an embed to the guild system channel about changes in guild
        Args can be some object or before, after objects

        :param event:
        :param guild:
        :param args:
        :return:
        """
        logging.info(f'The event "{event}" received')

        if not guild:
            return
        elif not guild.system_channel:
            return
        else:
            system_channel = guild.system_channel

        event_embed = discord.Embed()
        event_embed.title = f'Event ({event})'
        event_embed.timestamp = datetime.now(tz=pytz.timezone('Europe/Kiev'))

        event_type_upper = event.split('_').pop(-1).upper()

        if event_type_upper in ('CREATE', 'JOIN', 'ADD'):
            event_embed.color = discord.Color.brand_green()
            event_embed.set_author(name=guild.name, icon_url=guild.icon)
            event_embed.set_thumbnail(url=guild.icon)

            arg = args[0]

            try:
                if isinstance(arg, discord.Member):
                    arg_name = f'{arg.mention}'

                    event_embed.set_author(name=arg.name, icon_url=arg.avatar)
                    event_embed.set_thumbnail(url=arg.avatar)
                else:
                    arg_name = f'```{arg.name}```'
            except AttributeError:
                try:
                    arg_name = f'[link]({arg.url})'
                except AttributeError:
                    return

            event_embed.description = f"💥\n\n**{arg_name}**\n\n> {arg.__class__.__name__}"
        elif event_type_upper in ('UPDATE', 'EDIT'):
            event_embed.color = discord.Color.gold()
            event_embed.set_author(name=guild.name, icon_url=guild.icon)
            event_embed.set_thumbnail(url=guild.icon)

            arg = args[0]
            changes = ''

            if len(args) in (2, 3):
                if isinstance(args[1], datetime) or args[1] is None:
                    # date = datetime.strptime(args[1], '%Y-%m-%d %H:%M:%S%z').replace(tzinfo=pytz.utc).astimezone(tz=pytz.timezone('Europe/Kiev'))

                    if args[1]:
                        date = args[1].replace(tzinfo=pytz.utc).astimezone(tz=pytz.timezone('Europe/Kiev'))
                    else:
                        date = args[1]

                    changes = f'last_pin\n- ```{date}```'
                else:
                    if len(args) == 3:
                        before = args[1]
                        after = args[2]

                        event_embed.set_author(name=arg.name, icon_url=arg.avatar)
                        event_embed.set_thumbnail(url=arg.avatar)
                    else:
                        before = args[0]
                        after = args[1]

                        if isinstance(after, discord.Member):
                            event_embed.set_author(name=after.name, icon_url=after.avatar)
                            event_embed.set_thumbnail(url=after.avatar)

                    for attr in [attr for attr in dir(after) if not attr.startswith('_')]:
                        if not hasattr(before, attr):
                            continue

                        if not hasattr(after, attr):
                            continue

                        value_before = getattr(before, attr)
                        value_after = getattr(after, attr)

                        value = ''

                        if callable(value_after):
                            continue

                        if value_after != value_before:
                            if isinstance(value_after, list):
                                if tuple(value_before) == tuple(value_after):
                                    continue

                            if attr == 'clean_content':
                                value = f' - ```{value_before}``` ↓ ```{value_after}```'
                                changes = f'{changes}- {attr}\n{value}\n\n'
                                continue

                            # Skip attrs
                            if attr in (
                                'content',
                                'system_content',
                                'color',
                                'embeds',
                                'flags',
                                'tags',
                                # 'self_mute',
                                # 'self_deaf',
                                # 'self_stream',
                                # 'self_video',
                            ):
                                continue

                            if isinstance(value_after, dict):
                                overwrites_after = value_after.copy()

                                value_after = {}
                                for role_member, overwrite in overwrites_after.items():
                                    value_after[role_member.name] = [permission for permission, value in overwrite if value]

                                # value = ''
                                # for name, permissions in value_after.items():
                                #     value = f'{value}- `{name}` -> `{permissions}`\n'

                                value = '\n'.join([f'{value} - ```{name}``` ↓ ```{permissions}```' for name, permissions in value_after.items()])
                            elif isinstance(value_after, discord.Permissions):
                                permissions = [permission for permission, value in value_after if value]

                                value = f'{value} - ```{permissions}```'
                            elif isinstance(value_after, list) and (attr == 'roles' or attr == 'changed_roles'):
                                value = f" - ```{', '.join([role.name for role in value_after])}```"
                            else:
                                value = f' - ```{value_before}``` ↓ ```{value_after}```'

                            changes = f'{changes}- {attr}\n{value}\n\n'
            if not changes:
                return

            if isinstance(arg, discord.Member):
                arg_name = f'{arg.mention}'
            elif isinstance(arg, discord.Message):
                arg_name = f'{arg.author.mention}'
            else:
                arg_name = f'```{arg.name}```'

            event_embed.description = f"🚧\n\n**{arg_name}**\n\n> {arg.__class__.__name__}\n\n{changes}"
        elif event_type_upper in ('DELETE', 'REMOVE'):
            event_embed.color = discord.Color.brand_red()

            event_embed.set_author(name=guild.name, icon_url=guild.icon)
            event_embed.set_thumbnail(url=guild.icon)

            arg = args[0]
            fields = ''

            try:
                arg_name = f'```{arg.name}```'

                if isinstance(arg, discord.Member):
                    event_embed.set_author(name=arg.name, icon_url=arg.avatar)
                    event_embed.set_thumbnail(url=arg.avatar)

            except AttributeError:
                if isinstance(arg, discord.Invite):
                    arg_name = f'[link]({arg.url})'
                elif isinstance(arg, discord.Message):
                    arg_name = f'{arg.author.mention}'

                    if arg.clean_content:
                        fields = f'{fields}clean_content\n```{arg.clean_content}```'

                    if arg.attachments:
                        attachments = []
                        for attachment in arg.attachments:
                            attachments.append(attachment.url)
                        fields = f'{fields}attachments\n- {attachments}\n'

                    if arg.embeds:
                        embeds = []
                        for embed in arg.embeds:
                            if embed.title:
                                embeds.append(f"```{embed.title}```")
                                break

                            if embed.video:
                                embeds.append(embed.video.url)
                                break

                            if embed.image:
                                embeds.append(embed.image.url)
                                break

                        fields = f'{fields}embeds\n- {embeds}\n'
                else:
                    return

            event_embed.description = f"🧨\n\n**{arg_name}**\n\n> {arg.__class__.__name__}"

            if fields:
                event_embed.description = f'{event_embed.description}\n\n{fields}'

        try:
            await system_channel.send(embed=event_embed)
        except Exception:
            return

    async def _on_voice_state_leave(self, before, member):
        voice_channel = before.channel
        members = voice_channel.members
        guild = voice_channel.guild

        voice_channel_cache = cache.stats.get(guild.id, {}).get('tvoice_channels', {}).get(voice_channel.id, {})

        member_cache = cache.stats.get(guild.id, {}).get('members', {}).get(member.id, {})
        member_joined = member_cache.get('joined', '')
        if member_joined:
            voicetime = (datetime.now(tz=pytz.utc).replace(tzinfo=None) - datetime.strptime(member_joined,
                                                                                            '%Y-%m-%d %H:%M:%S')).total_seconds()

            # was in voice 6.9 hours (24840 seconds) or more
            if voicetime >= 24840:
                # Chance to get role for being in voice channel 6.9 or more hours
                await secret_roles(member=member, guild=guild, event='being in voice channel 6.9 or more hours')

            voicetime += member_cache.get('voicetime', 0)

            cache.stats[guild.id]['members'][member.id]['voicetime'] = voicetime
            del cache.stats[guild.id]['members'][member.id]['joined']

        if voice_channel_cache:
            if len(members) == 0:
                # Leaves last member in voice channel
                try:
                    await voice_channel.delete()
                except discord.errors.NotFound:
                    pass

                del cache.stats[guild.id]['tvoice_channels'][voice_channel.id]

                # Chance to get role for leaving last from temporary voice channel
                await secret_roles(member=member, guild=guild, event='leaving last from temporary voice channel')

                return

            if len(members) == 1:
                if members[0].bot:
                    # Bot last member in voice channel
                    voice_client = guild.voice_client

                    if voice_client:
                        await voice_client.disconnect()

                    try:
                        await voice_channel.delete()
                    except discord.errors.NotFound:
                        pass

                    del cache.stats[guild.id]['tvoice_channels'][voice_channel.id]

                    return

            if member.bot:
                return -1

            # Leaves not last member in voice channel
            owner = voice_channel_cache.get('owner', {})

            if owner.get('id', '') == member.id:
                # Leaves owner of voice channel
                new_owner = None

                for tmember in members:
                    if not tmember.bot:
                        new_owner = tmember

                if new_owner:
                    overwrites = voice_channel.overwrites
                    overwrites[new_owner] = discord.PermissionOverwrite.from_pair(allow=discord.Permissions.all_channel(), deny=discord.Permissions.none())

                    # Restrict pvevious owner of voice channel to only view voice channel
                    # del overwrites[member]
                    allow = discord.Permissions.none()
                    allow.view_channel = True
                    overwrites[member] = discord.PermissionOverwrite.from_pair(allow=allow, deny=discord.Permissions.none())

                    await voice_channel.edit(name=f'@{new_owner.name}', overwrites=overwrites)

                    cache.stats[guild.id]['tvoice_channels'][voice_channel.id]['owner']['id'] = new_owner.id
        else:
            # Not temporary voice channel

            # In voice channel left more than 1 member
            if len(members) > 1:
                return

            # Last member in voice channel is not bot
            if len(members) == 1:
                if not members[0].bot:
                    return

            # No one in voice channel or only bot in voice channel
            guild_cache = self.discordBot.guilds.get(guild.id, {})
            if not guild_cache:
                return

            init_channel = guild_cache.get('temporary', {}).get('inits', {}).get(f'{voice_channel.id}', '')

            # Delete voice channel if it is not init voice channel
            if not init_channel:
                voice_client = guild.voice_client

                if voice_client:
                    await voice_client.disconnect()

                try:
                    return await voice_channel.delete()
                except discord.errors.NotFound:
                    pass

    async def _on_voice_state_join(self, after, member):
        voice_channel = after.channel
        guild = voice_channel.guild

        guild_cache = self.discordBot.guilds.get(guild.id, {})
        if not guild_cache:
            return -1

        init_channel = guild_cache.get('temporary', {}).get('inits', {}).get(f'{voice_channel.id}', '')

        if init_channel:
            category = voice_channel.category

            overwrites = {
                member: discord.PermissionOverwrite.from_pair(allow=discord.Permissions.all_channel(), deny=discord.Permissions.none())
            }

            if category:
                voice_channel = await category.create_voice_channel(name=f'@{member.name}',
                                                                    position=voice_channel.position + 1,
                                                                    overwrites=overwrites)
            else:
                voice_channel = await guild.create_voice_channel(name=f'@{member.name}',
                                                                 position=voice_channel.position + 1,
                                                                 overwrites=overwrites)

            cache.stats[guild.id]['tvoice_channels'][voice_channel.id]['owner']['id'] = member.id

            try:
                await member.move_to(channel=voice_channel)

                # Chance to get role for creation of new temporary voice channel
                await secret_roles(member=member, guild=guild, event='creation of new temporary voice channel')
            except discord.HTTPException:
                if len(voice_channel.members) == 0:
                    await voice_channel.delete()

            # await voice_channel.set_permissions(member, overwrite=discord.PermissionOverwrite.from_pair(allow=discord.Permissions.all_channel(), deny=discord.Permissions.none()))

            # self.discordBot.guilds[guild.id]['temporary']['channels'][f'{voice_channel.id}']= {'owner': {'id': member.id}}
        else:
            # Joined not in init channel
            date = datetime.now(tz=pytz.utc)
            date = date.strftime('%Y-%m-%d %H:%M:%S')

            cache.stats[guild.id]['members'][member.id]['joined'] = date

            # Chance to get role for joining voice channel
            await secret_roles(member=member, guild=guild, event='joining voice channel')

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

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        """
        Called when a Member changes their VoiceState.

        The following, but not limited to, examples illustrate when this event is called:
            A member joins a voice or stage channel.
            A member leaves a voice or stage channel.
            A member is muted or deafened by their own accord.
            A member is muted or deafened by a guild administrator.

        This requires Intents.voice_states to be enabled.

        :param member:
        :param before:
        :param after:
        :return:
        """
        await self._on_event_send_embed('on_voice_state_update', member.guild, member, before, after)
        # if member == client.user:
        #    return

        # if member.bot:
        #    return

        if not before.self_deaf == after.self_deaf:
            # print('self deaf')
            if after.self_deaf:
                guild = member.guild

                if not guild:
                    return

                # Chance to get role for self deaf action
                await secret_roles(member=member, guild=guild, event='self deaf action')

        if not before.self_mute == after.self_mute:
            # print('self mute')
            if after.self_mute:
                guild = member.guild

                if not guild:
                    return

                # Chance to get role for self mute action
                await secret_roles(member=member, guild=guild, event='self mute action')

        if not before.self_video == after.self_video:
            # print('video')
            if after.self_video:
                guild = member.guild

                if not guild:
                    return

                # Chance to get role for self video action
                await secret_roles(member=member, guild=guild, event='self video action')

        if not before.self_stream == after.self_stream:
            # print('stream')

            if after.self_stream:
                guild = member.guild

                if not guild:
                    return

                # Chance to get role for self stream action
                await secret_roles(member=member, guild=guild, event='self stream action')

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
            if await self._on_voice_state_leave(before=before, member=member) == -1:
                return

        if after.channel is not None:
            if before.channel:
                if before.channel == after.channel:
                    return

            # User join voice channel
            if await self._on_voice_state_join(after=after, member=member) == -1:
                return

    async def on_ready(self):
        """
        Called when the client is done preparing the data received from Discord. Usually after login is successful and the Client.guilds and co. are filled up.
        """
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
        activity = discord.CustomActivity(name=f"v{__version__} | {updated}")

        await self.discordBot.client.change_presence(status=status, activity=activity)

    async def _on_resumed(self):
        """
        Called when the client has resumed a session.
        """
        pass

    async def _on_shard_ready(self, shard_id: int):
        """
        Similar to on_ready() except used by AutoShardedClient to denote when a particular shard ID has become ready.
        """
        pass

    async def _on_shard_resumed(self, shard_id: int):
        """
        Similar to on_resumed() except used by AutoShardedClient to denote when a particular shard ID has resumed a session.
        """
        pass

    async def _on_message_count(self, guild, author):
        last_message = cache.stats[guild.id]['members'][author.id]['last_message']
        last_message_seconds = None
        if last_message:
            last_message_seconds = (datetime.now(tz=pytz.utc).replace(tzinfo=None) - datetime.strptime(last_message,'%Y-%m-%d %H:%M:%S')).total_seconds()

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

    async def on_message(self, message: discord.Message):
        """
        Called when a Message is created and sent.

        This requires Intents.messages to be enabled.

        :param message:
        :return:
        """
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

            # Count messages
            await self._on_message_count(guild=guild, author=author)

            # Unique roles
            content = message.content.lower()

            await secret_roles(author, guild, 'sending message', content)

        except Exception as e:
            logging.warning(e)

    async def _on_error(self, event: str, *args, **kwargs):
        """
        args
        {
            "message": "A message saying you are being rate limited",
            "retry_after": "The number of seconds to wait before submitting another request",
            "global": "A value indicating if you are being globally rate limited or not",
            "code?": "An error code for some limits",
        }

        Usually when an event raises an uncaught exception, a traceback is logged to stderr and the exception is ignored. If you want to change this behaviour and handle the exception for whatever reason yourself, this event can be overridden. Which, when done, will suppress the default action of printing the traceback.

        The information of the exception raised and the exception itself can be retrieved with a standard call to sys.exc_info().
        """

        # if type(args[1]) == type(int):
        #     return await asyncio.sleep(args[1])

        # print(event, args, kwargs)
        pass

    async def _on_socket_event_type(self, event_type: str):
        """
        Called whenever a websocket event is received from the WebSocket.

        This is mainly useful for logging how many events you are receiving from the Discord gateway.
        """
        # print(event_type)
        pass

    async def _on_socket_raw_receive(self, msg: str):
        """
        Called whenever a message is completely received from the WebSocket, before it’s processed and parsed. This event is always dispatched when a complete message is received and the passed data is not parsed in any way.

        This is only really useful for grabbing the WebSocket stream and debugging purposes.

        This requires setting the enable_debug_events setting in the Client.
        """
        pass

    async def _on_socket_raw_send(self, payload: Union[bytes, str]):
        """
        Called whenever a send operation is done on the WebSocket before the message is sent. The passed parameter is the message that is being sent to the WebSocket.

        This is only really useful for grabbing the WebSocket stream and debugging purposes.

        This requires setting the enable_debug_events setting in the Client.
        """
        pass

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """
        Called when a Message receives an update event. If the message is not found in the internal message cache, then these events will not be called. Messages might not be in cache if the message is too old or the client is participating in high traffic guilds.

        If this occurs increase the max_messages parameter or use the on_raw_message_edit() event instead.

        The following non-exhaustive cases trigger this event:
            A message has been pinned or unpinned.
            The message content has been changed.
            The message has received an embed. For performance reasons, the embed server does not do this in a “consistent” manner.
            The message’s embeds were suppressed or unsuppressed.
            A call message has received an update to its participants or ending time.

        This requires Intents.messages to be enabled.

        :param before:
        :param after:
        """

        if not after.guild:
            return

        guild = after.guild
        member = after.author

        if member.bot:
            return

        await self._on_event_send_embed('on_message_edit', guild, before, after)

        # Chance to get role for editing message
        await secret_roles(member=member, guild=guild, event='editing message')

    async def on_message_delete(self, message: discord.Message):
        """
        Called when a message is deleted. If the message is not found in the internal message cache, then this event will not be called. Messages might not be in cache if the message is too old or the client is participating in high traffic guilds.

        If this occurs increase the max_messages parameter or use the on_raw_message_delete() event instead.

        This requires Intents.messages to be enabled.
        """

        if not message.guild:
            return

        guild = message.guild
        member = message.author

        await self._on_event_send_embed('on_message_delete', guild, message)

        await secret_roles(member=member, guild=guild, event='deleting message')

    async def _on_bulk_message_delete(self, messages: list[discord.Message]):
        """
        Called when messages are bulk deleted. If none of the messages deleted are found in the internal message cache, then this event will not be called. If individual messages were not found in the internal message cache, this event will still be called, but the messages not found will not be included in the messages list. Messages might not be in cache if the message is too old or the client is participating in high traffic guilds.

        If this occurs increase the max_messages parameter or use the on_raw_bulk_message_delete() event instead.

        This requires Intents.messages to be enabled.
        """
        pass

    async def _on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        """
        Called when a message is edited. Unlike on_message_edit(), this is called regardless of the state of the internal message cache.

        If the message is found in the message cache, it can be accessed via RawMessageUpdateEvent.cached_message. The cached message represents the message before it has been edited. For example, if the content of a message is modified and triggers the on_raw_message_edit() coroutine, the RawMessageUpdateEvent.cached_message will return a Message object that represents the message before the content was modified.

        Due to the inherently raw nature of this event, the data parameter coincides with the raw data given by the gateway.

        Since the data payload can be partial, care must be taken when accessing stuff in the dictionary. One example of a common case of partial data is when the 'content' key is inaccessible. This denotes an “embed” only edit, which is an edit in which only the embeds are updated by the Discord embed server.

        This requires Intents.messages to be enabled.
        """
        pass

    async def _on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        """
        Called when a message is deleted. Unlike on_message_delete(), this is called regardless of the message being in the internal message cache or not.

        If the message is found in the message cache, it can be accessed via RawMessageDeleteEvent.cached_message

        This requires Intents.messages to be enabled.
        """
        # if not payload.guild_id:
        #     return
        #
        # print(payload)
        #
        # guild: discord.abc.Guild = self.discordBot.client.get_guild(payload.guild_id)
        # message: discord.Message = payload.cached_message
        #
        # if message:
        #     await self._on_event_send_embed('on_raw_message_delete', guild, message)
        #     member = message.author
        #
        #     await secret_roles(member=member, guild=guild, event='deleting message')
        pass

    async def _on_raw_bulk_message_delete(self, payload: discord.RawBulkMessageDeleteEvent):
        """
        Called when a bulk delete is triggered. Unlike on_bulk_message_delete(), this is called regardless of the messages being in the internal message cache or not.

        If the messages are found in the message cache, they can be accessed via RawBulkMessageDeleteEvent.cached_messages

        This requires Intents.messages to be enabled.
        """
        pass

    async def on_raw_app_command_permissions_update(self, payload: discord.RawAppCommandPermissionsUpdateEvent):
        """
        Called when application command permissions are updated.
        """
        await self._on_event_send_embed('on_raw_app_command_permissions_update', payload.guild, payload)

    async def _on_app_command_completion(self, interaction: discord.Interaction, command: Union[
        discord.app_commands.Command, discord.app_commands.ContextMenu]):
        """
        Called when a app_commands.Command or app_commands.ContextMenu has successfully completed without error.
        """
        pass

    async def on_automod_rule_create(self, rule: discord.AutoModRule):
        """
        Called when a AutoModRule is created. You must have manage_guild to receive this.

        This requires Intents.auto_moderation_configuration to be enabled.
        """
        await self._on_event_send_embed('on_automod_rule_create', rule.guild, rule)

    async def on_automod_rule_update(self, rule: discord.AutoModRule):
        """
        Called when a AutoModRule is updated. You must have manage_guild to receive this.

        This requires Intents.auto_moderation_configuration to be enabled.
        """
        await self._on_event_send_embed('on_automod_rule_update', rule.guild, rule)

    async def on_automod_rule_delete(self, rule: discord.AutoModRule):
        """
        Called when a AutoModRule is deleted. You must have manage_guild to receive this.

        This requires Intents.auto_moderation_configuration to be enabled.
        """
        await self._on_event_send_embed('on_automod_rule_delete', rule.guild, rule)

    async def _on_automod_action(self, rule: discord.AutoModRule):
        """
        Called when a AutoModAction is created/performed. You must have manage_guild to receive this.

        This requires Intents.auto_moderation_execution to be enabled.
        """
        pass

    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        """
        Called whenever a guild channel is deleted or created.

        Note that you can get the guild from guild.

        This requires Intents.guilds to be enabled.
        """
        await self._on_event_send_embed('on_guild_channel_create', channel.guild, channel)

    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        """
        Called whenever a guild channel is deleted or created.

        Note that you can get the guild from guild.

        This requires Intents.guilds to be enabled.
        """
        await self._on_event_send_embed('on_guild_channel_delete', channel.guild, channel)

    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        """
        Called whenever a guild channel is updated. e.g. changed name, topic, permissions.

        This requires Intents.guilds to be enabled.
        """
        await self._on_event_send_embed('on_guild_channel_update', after.guild, before, after)

    async def on_guild_channel_pins_update(self, channel: Union[discord.abc.GuildChannel, discord.Thread],
                                           last_pin: Optional[datetime]):
        """
        Called whenever a message is pinned or unpinned from a guild channel.

        This requires Intents.guilds to be enabled.
        """
        await self._on_event_send_embed('on_guild_channel_pins_update', channel.guild, channel, last_pin)

    async def _on_private_channel_update(self, before: discord.GroupChannel, after: discord.GroupChannel):
        """
        Called whenever a private group DM is updated. e.g. changed name or topic.

        This requires Intents.messages to be enabled.
        """
        pass

    async def _on_private_channel_pins_update(self, channel: discord.abc.PrivateChannel, last_pin: Optional[datetime]):
        """
        Called whenever a message is pinned or unpinned from a private channel.
        """
        pass

    async def _on_typing(self, channel: discord.abc.Messageable, user: Union[discord.User, discord.Member],
                         when: datetime):
        """
        Called when someone begins typing a message.

        The channel parameter can be a abc.Messageable instance. Which could either be TextChannel, GroupChannel, or DMChannel.

        If the channel is a TextChannel then the user parameter is a Member, otherwise it is a User.

        If the channel or user could not be found in the internal cache this event will not be called, you may use on_raw_typing() instead.

        This requires Intents.typing to be enabled.
        """
        pass

    async def _on_raw_typing(self, payload: discord.RawTypingEvent):
        """
        Called when someone begins typing a message. Unlike on_typing() this is called regardless of the channel and user being in the internal cache.

        This requires Intents.typing to be enabled.
        """
        pass

    async def _on_connect(self):
        """
        Called when the client has successfully connected to Discord. This is not the same as the client being fully prepared, see on_ready() for that.

        The warnings on on_ready() also apply.
        """
        pass

    async def _on_disconnect(self):
        """
        Called when the client has disconnected from Discord, or a connection attempt to Discord has failed. This could happen either through the internet being disconnected, explicit calls to close, or Discord terminating the connection one way or the other.

        This function can be called many times without a corresponding on_connect() call.
        """
        pass

    async def _on_shard_connect(self, shard_id: int):
        """
        Similar to on_connect() except used by AutoShardedClient to denote when a particular shard ID has connected to Discord.
        """
        pass

    async def _on_shard_disconnect(self, shard_id: int):
        """
        Similar to on_disconnect() except used by AutoShardedClient to denote when a particular shard ID has disconnected from Discord.
        """
        pass

    async def _on_guild_available(self, guild: discord.Guild):
        """
        Called when a guild becomes available or unavailable. The guild must have existed in the Client.guilds cache.

        This requires Intents.guilds to be enabled.
        """
        pass

    async def _on_guild_unavailable(self, guild: discord.Guild):
        """
        Called when a guild becomes available or unavailable. The guild must have existed in the Client.guilds cache.

        This requires Intents.guilds to be enabled.
        """
        pass

    async def _on_guild_join(self, guild: discord.Guild):
        """
        Called when a Guild is either created by the Client or when the Client joins a guild.

        This requires Intents.guilds to be enabled.
        """

        # query = {f'guilds.id': guild.id}
        # filter = {'id': guild.id}
        #
        # if self.mongoDataBase.update_field(database_name='dbot', collection_name='guilds', action='$set', query=query,
        #                                    filter=filter) is None:
        #     print('Guild not added to DataBase')
        await self._on_event_send_embed('on_guild_join', guild, guild)

    async def _on_guild_remove(self, guild: discord.Guild):
        """
        Called when a Guild is removed from the Client.

        This happens through, but not limited to, these circumstances:
            The client got banned.
            The client got kicked.
            The client left the guild.
            The client or the guild owner deleted the guild.

        In order for this event to be invoked then the Client must have been part of the guild to begin with. (i.e. it is part of Client.guilds)

        This requires Intents.guilds to be enabled.
        """
        await self._on_event_send_embed('on_guild_remove', guild, guild)

    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        """
        Called when a Guild updates, for example:
            Changed name
            Changed AFK channel
            Changed AFK timeout
            etc

        This requires Intents.guilds to be enabled.
        """
        await self._on_event_send_embed('on_guild_update', after, before, after)

    async def on_guild_emojis_update(self, guild: discord.Guild, before: discord.abc.Sequence[discord.Emoji],
                                     after: discord.abc.Sequence[discord.Emoji]):
        """
        Called when a Guild adds or removes Emoji.

        This requires Intents.emojis_and_stickers to be enabled.
        """
        await self._on_event_send_embed('on_guild_emojis_update', guild, before, after)

    async def on_guild_stickers_update(self, guild: discord.Guild, before: discord.abc.Sequence[discord.Sticker],
                                       after: discord.abc.Sequence[discord.Sticker]):
        """
        Called when a Guild updates its stickers.

        This requires Intents.emojis_and_stickers to be enabled.
        """
        await self._on_event_send_embed('on_guild_stickers_update', guild, before, after)

    async def _on_audit_log_entry_create(self, entry: discord.AuditLogEntry):
        """
        Called when a Guild gets a new audit log entry. You must have view_audit_log to receive this.

        This requires Intents.moderation to be enabled.
        """
        # if entry.action == discord.AuditLogAction.message_delete:
        #     member = entry.user
        #     guild = entry.guild
        #
        #     if isinstance(member, discord.Member):
        #         # Chance to get role for deleting message
        #         await secret_roles(member=member, guild=guild, event='deleting message')

        await self._on_event_send_embed('on_audit_log_entry_create', entry.guild, entry)

    async def on_invite_create(self, invite: discord.Invite):
        """
        Called when an Invite is created. You must have manage_channels to receive this.
        """
        if not invite.guild:
            return

        guild = invite.guild
        member = invite.inviter

        await self._on_event_send_embed('on_invite_create', guild, invite)

        # Chance to get role for creating invite
        await secret_roles(member=member, guild=guild, event='creating invite')

    async def on_invite_delete(self, invite: discord.Invite):
        """
        Called when an Invite is deleted. You must have manage_channels to receive this.
        """
        await self._on_event_send_embed('on_invite_delete', invite.guild, invite)

    async def on_integration_create(self, intergration: discord.Integration):
        """
        Called when an integration is created.

        This requires Intents.integrations to be enabled.
        """
        await self._on_event_send_embed('on_integration_create', intergration.guild, intergration)

    async def on_integration_update(self, intergration: discord.Integration):
        """
        Called when an integration is updated.

        This requires Intents.integrations to be enabled.
        """
        await self._on_event_send_embed('on_integration_update', intergration.guild, intergration)

    async def on_guild_integrations_update(self, guild: discord.Guild):
        """
        Called whenever an integration is created, modified, or removed from a guild.

        This requires Intents.integrations to be enabled.
        """
        await self._on_event_send_embed('on_guild_integrations_update', guild, guild)

    async def on_webhooks_update(self, channel: discord.abc.GuildChannel):
        """
        Called whenever a webhook is created, modified, or removed from a guild channel.

        This requires Intents.webhooks to be enabled.
        """
        await self._on_event_send_embed('on_webhooks_update', channel.guild, channel)

    async def _on_raw_integration_delete(self, payload: discord.RawIntegrationDeleteEvent):
        """
        Called when an integration is deleted.

        This requires Intents.integrations to be enabled.
        """
        pass

    async def _on_interaction(self, interaction: discord.Interaction):
        """
        Called when an interaction happened.

        This currently happens due to slash command invocations or components being used.
        """
        pass

    async def on_member_join(self, member: discord.Member):
        """
        Called when a Member joins a Guild.

        This requires Intents.members to be enabled.
        """
        await self._on_event_send_embed('on_member_join', member.guild, member)

    async def on_member_remove(self, member: discord.Member):
        """
        Called when a Member leaves a Guild.

        If the guild or member could not be found in the internal cache this event will not be called, you may use on_raw_member_remove() instead.

        This requires Intents.members to be enabled.
        """
        await self._on_event_send_embed('on_member_remove', member.guild, member)

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """
        Called when a Member updates their profile.

        This is called when one or more of the following things change:
            nickname
            roles
            pending
            timeout
            guild avatar
            flags

        Due to a Discord limitation, this event is not dispatched when a member’s timeout expires.

        This requires Intents.members to be enabled.
        """
        await self._on_event_send_embed('on_member_update', after.guild, before, after)

    async def _on_raw_member_remove(self, payload: discord.RawMemberRemoveEvent):
        """
        Called when a Member leaves a Guild.

        Unlike on_member_remove() this is called regardless of the guild or member being in the internal cache.

        This requires Intents.members to be enabled.
        """
        pass

    async def _on_user_update(self, before: discord.User, after: discord.User):
        """
        Called when a User updates their profile.

        This is called when one or more of the following things change:
            avatar
            username
            discriminator

        This requires Intents.members to be enabled.
        """
        await self._on_event_send_embed('on_user_update', None, before, after)

    async def _on_member_ban(self, guild: discord.Guild, user: Union[discord.User, discord.Member]):
        """
        Called when user gets banned from a Guild.

        This requires Intents.moderation to be enabled.
        """
        pass

    async def _on_member_unban(self, guild: discord.Guild, user: discord.User):
        """
        Called when a User gets unbanned from a Guild.

        This requires Intents.moderation to be enabled.
        """
        pass

    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        """
        Called when a Member updates their presence.

        This is called when one or more of the following things change:
            status
            activity

        This requires Intents.presences and Intents.members to be enabled.
        """
        # await self._on_event_send_embed('on_presence_update', after.guild, before, after)

        if before.activities != after.activities:
            await secret_roles(after, after.guild, 'activity updated', after.activity)

    async def _on_reaction_add_count(self, guild: discord.Guild, author: discord.Member):
        reactions_count = 1
        reactions_count += cache.stats.get(guild.id, {}).get('members', {}).get(author.id, {}).get('reactions_count', 0)

        cache.stats[guild.id]['members'][author.id]['reactions_count'] = reactions_count

    async def on_reaction_add(self, reaction: discord.Reaction, user: Union[discord.Member, discord.User]):
        """
        Called when a message has a reaction added to it. Similar to on_message_edit(), if the message is not found in the internal message cache, then this event will not be called. Consider using on_raw_reaction_add() instead.

        This requires Intents.reactions to be enabled.
        """
        if not isinstance(user, discord.Member):
            return

        member = user
        guild = member.guild

        if not user == reaction.message.author:
            # Reaction count
            await self._on_reaction_add_count(guild=guild, author=reaction.message.author)

        await self._on_event_send_embed('on_reaction_add', guild, reaction)

        # Chance to get role for adding reaction to message
        await secret_roles(member, guild, 'adding reaction to message', reaction.emoji)

    async def _on_reaction_remove_count(self, guild: discord.Guild, author: discord.Member):
        reactions_count = -1
        reactions_count += cache.stats.get(guild.id, {}).get('members', {}).get(author.id, {}).get('reactions_count', 0)

        cache.stats[guild.id]['members'][author.id]['reactions_count'] = reactions_count

    async def on_reaction_remove(self, reaction: discord.Reaction, user: Union[discord.Member, discord.User]):
        """
        Called when a message has a reaction removed from it. Similar to on_message_edit, if the message is not found in the internal message cache, then this event will not be called.

        This requires both Intents.reactions and Intents.members to be enabled.
        """
        if not isinstance(user, discord.Member):
            return

        member = user
        guild = member.guild

        if not user == reaction.message.author:
            # Reaction count
            await self._on_reaction_remove_count(guild=guild, author=reaction.message.author)

        await self._on_event_send_embed('on_reaction_remove', guild, reaction)

        # Chance to get role for removing reaction from message
        await secret_roles(member=member, guild=guild, event='removing reaction from message')

    async def _on_reaction_clear(self, message: discord.Message, reactions: list[discord.Reaction]):
        """
        Called when a message has all its reactions removed from it. Similar to on_message_edit(), if the message is not found in the internal message cache, then this event will not be called. Consider using on_raw_reaction_clear() instead.

        This requires Intents.reactions to be enabled.
        """
        pass

    async def _on_reaction_clear_emoji(self, reaction: discord.Reaction):
        """
        Called when a message has a specific reaction removed from it. Similar to on_message_edit(), if the message is not found in the internal message cache, then this event will not be called. Consider using on_raw_reaction_clear_emoji() instead.

        This requires Intents.reactions to be enabled.
        """
        pass

    async def _on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """
        Called when a message has a reaction added. Unlike on_reaction_add(), this is called regardless of the state of the internal message cache.

        This requires Intents.reactions to be enabled.
        """
        pass

    async def _on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """
        Called when a message has a reaction removed. Unlike on_reaction_remove(), this is called regardless of the state of the internal message cache.

        This requires Intents.reactions to be enabled.
        """
        pass

    async def _on_raw_reaction_clear(self, payload: discord.RawReactionClearEvent):
        """
        Called when a message has all its reactions removed. Unlike on_reaction_clear(), this is called regardless of the state of the internal message cache.

        This requires Intents.reactions to be enabled.
        """
        pass

    async def _on_raw_reaction_clear_emoji(self, payload: discord.RawReactionClearEmojiEvent):
        """
        Called when a message has a specific reaction removed from it. Unlike on_reaction_clear_emoji() this is called regardless of the state of the internal message cache.

        This requires Intents.reactions to be enabled.
        """
        pass

    async def on_guild_role_create(self, role: discord.Role):
        """
        Called when a Guild creates or deletes a new Role.

        To get the guild it belongs to, use Role.guild.

        This requires Intents.guilds to be enabled.
        """
        await self._on_event_send_embed('on_guild_role_create', role.guild, role)

    async def on_guild_role_delete(self, role: discord.Role):
        """
        Called when a Guild creates or deletes a new Role.

        To get the guild it belongs to, use Role.guild.

        This requires Intents.guilds to be enabled.
        """
        await self._on_event_send_embed('on_guild_role_delete', role.guild, role)

    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        """
        Called when a Role is changed guild-wide.

        This requires Intents.guilds to be enabled.
        """
        await self._on_event_send_embed('on_guild_role_update', after.guild, before, after)

    async def on_scheduled_event_create(self, event: discord.ScheduledEvent):
        """
        Called when a ScheduledEvent is created or deleted.

        This requires Intents.guild_scheduled_events to be enabled.
        """
        await self._on_event_send_embed('on_scheduled_event_create', event.guild, event)

    async def on_scheduled_event_delete(self, event: discord.ScheduledEvent):
        """
        Called when a ScheduledEvent is created or deleted.

        This requires Intents.guild_scheduled_events to be enabled.
        """
        await self._on_event_send_embed('on_scheduled_event_delete', event.guild, event)

    async def on_scheduled_event_update(self, before: discord.ScheduledEvent, after: discord.ScheduledEvent):
        """
        Called when a ScheduledEvent is updated.

        This requires Intents.guild_scheduled_events to be enabled.

        The following, but not limited to, examples illustrate when this event is called:
            The scheduled start/end times are changed.
            The channel is changed.
            The description is changed.
            The status is changed.
            The image is changed.
        """
        await self._on_event_send_embed('on_scheduled_event_update', after.guild, before, after)

    async def on_scheduled_event_user_add(self, event: discord.ScheduledEvent, user: discord.User):
        """
        Called when a user is added or removed from a ScheduledEvent.

        This requires Intents.guild_scheduled_events to be enabled.
        """
        await self._on_event_send_embed('on_scheduled_event_user_add', event.guild, user)

    async def on_scheduled_event_user_remove(self, event: discord.ScheduledEvent, user: discord.User):
        """
        Called when a user is added or removed from a ScheduledEvent.

        This requires Intents.guild_scheduled_events to be enabled.
        """
        await self._on_event_send_embed('on_scheduled_event_user_remove', event.guild, user)

    async def on_stage_instance_create(self, stage_instance: discord.StageInstance):
        """
        Called when a StageInstance is created or deleted for a StageChannel.
        """
        await self._on_event_send_embed('on_stage_instance_create', stage_instance.guild, stage_instance)

    async def on_stage_instance_delete(self, stage_instance: discord.StageInstance):
        """
        Called when a StageInstance is created or deleted for a StageChannel.
        """
        await self._on_event_send_embed('on_stage_instance_delete', stage_instance.guild, stage_instance)

    async def on_stage_instance_update(self, before: discord.StageInstance, after: discord.StageInstance):
        """
        Called when a StageInstance is updated.

        The following, but not limited to, examples illustrate when this event is called:
            The topic is changed.
            The privacy level is changed.
        """
        await self._on_event_send_embed('on_stage_instance_update', after.guild, before, after)

    async def on_thread_create(self, thread: discord.Thread):
        """
        Called whenever a thread is created.

        Note that you can get the guild from Thread.guild.

        This requires Intents.guilds to be enabled.
        """

        guild = thread.guild

        await self._on_event_send_embed('on_thread_create', guild, thread)

        # Chance to get role for creation of thread
        await secret_roles(member=thread.owner, guild=guild, event='creation of thread')

    async def on_thread_join(self, thread: discord.Thread):
        """
        Called whenever a thread is joined.

        Note that you can get the guild from Thread.guild.

        This requires Intents.guilds to be enabled.
        """
        await self._on_event_send_embed('on_thread_join', thread.guild, thread)

    async def on_thread_remove(self, thread: discord.Thread):
        """
        Called whenever a thread is removed. This is different from a thread being deleted.

        Note that you can get the guild from Thread.guild.

        This requires Intents.guilds to be enabled.
        """
        await self._on_event_send_embed('on_thread_remove', thread.guild, thread)

    async def on_thread_update(self, before: discord.Thread, after: discord.Thread):
        """
        Called whenever a thread is updated. If the thread could not be found in the internal cache this event will not be called. Threads will not be in the cache if they are archived.

        If you need this information use on_raw_thread_update() instead.

        This requires Intents.guilds to be enabled.
        """
        await self._on_event_send_embed('on_thread_update', after.guild, before, after)

    async def on_thread_delete(self, thread: discord.Thread):
        """
        Called whenever a thread is deleted. If the thread could not be found in the internal cache this event will not be called. Threads will not be in the cache if they are archived.

        If you need this information use on_raw_thread_delete() instead.

        Note that you can get the guild from Thread.guild.

        This requires Intents.guilds to be enabled.
        """
        await self._on_event_send_embed('on_thread_delete', thread.guild, thread)

    async def _on_raw_thread_update(self, payload: discord.RawThreadUpdateEvent):
        """
        Called whenever a thread is updated. Unlike on_thread_update() this is called regardless of the thread being in the internal thread cache or not.

        This requires Intents.guilds to be enabled.
        """
        guild = self.discordBot.client.get_guild(payload.guild_id)
        thread = guild.get_thread(payload.thread_id)
        await self._on_event_send_embed('on_raw_thread_update', guild, thread)

    async def _on_raw_thread_delete(self, payload: discord.RawThreadDeleteEvent):
        """
        Called whenever a thread is deleted. Unlike on_thread_delete() this is called regardless of the thread being in the internal thread cache or not.

        This requires Intents.guilds to be enabled.
        """
        pass

    async def on_thread_member_join(self, member: discord.ThreadMember):
        """
        Called when a ThreadMember joins a Thread.

        You can get the thread a member belongs in by accessing ThreadMember.thread.

        This requires Intents.members to be enabled.
        """
        await self._on_event_send_embed('on_thread_member_join', member.thread.guild, member)

    async def on_thread_member_remove(self, member: discord.ThreadMember):
        """
        Called when a ThreadMember leaves a Thread.

        You can get the thread a member belongs in by accessing ThreadMember.thread.

        This requires Intents.members to be enabled.
        """
        await self._on_event_send_embed('on_thread_member_remove', member.thread.guild, member)

    async def _on_raw_thread_member_remove(self, payload: discord.RawThreadMembersUpdate):
        """
        Called when a ThreadMember leaves a Thread. Unlike on_thread_member_remove() this is called regardless of the member being in the internal thread’s members cache or not.

        This requires Intents.members to be enabled.
        """
        pass
