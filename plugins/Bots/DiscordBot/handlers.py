import asyncio
import os
import discord.ext.commands
import pytz
import utils

from datetime import datetime
from plugins.DataBase.mongo import MongoDataBase
from version import __version__
from utils import *

class DiscordBotHandler:
    """
    DiscordBot Handler
    """

    def __init__(self, webSerber, discordBot, mongoDataBase: MongoDataBase):
        self.webServer = webSerber
        self.discordBot = discordBot
        self.mongoDataBase = mongoDataBase

        # register handlers
        for handler in [handler for handler in dir(DiscordBotHandler) if not handler.startswith('__')]:
            callback = getattr(self, handler)
            self.discordBot.client.event(callback)

    # ------------------------------------------------------------------------------------------------------------------
    # EVENTS -----------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        try:
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

            if before.channel:
                # User moved or leaves voice channel
                voice_channel = before.channel
                members = voice_channel.members
                guild = voice_channel.guild

                # Get data from database
                # query = {'_id': 0, 'temporary': 1, 'members': 1}
                # filter = {'id': guild.id}
                # document = self.mongoDataBase.get_document(database_name='dbot', collection_name='guilds', query=query, filter=filter)
                guild_cache = self.discordBot.guilds.get(guild.id, {})
                if not guild_cache:
                    return
                # if not document:
                #     return

                joined = guild_cache.get('members', {}).get(f'{member.id}', {}).get('stats', {}).get('joined', '')

                if joined:
                    voicetime = (datetime.now(tz=pytz.utc).replace(tzinfo=None) - datetime.strptime(joined,
                                                                                                    '%Y-%m-%d %H:%M:%S')).total_seconds()

                    query = {f'members.{member.id}.stats.voicetime': voicetime}
                    filter = {'id': guild.id}

                    mongoUpdate = self.mongoDataBase.update_field(database_name='dbot', collection_name='guilds', action='$inc', filter=filter, query=query)

                    if mongoUpdate is None:
                        print('Not updated voicetime of member in DataBase')
                    else:
                        self.discordBot.guilds[guild.id] = mongoUpdate

                    query = {f'members.{member.id}.stats.joined': ''}
                    filter = {'id': guild.id}

                    mongoUpdate = self.mongoDataBase.update_field(database_name='dbot', collection_name='guilds', action='$unset', filter=filter, query=query)

                    if mongoUpdate is None:
                        print('Not updated joined of member in DataBase')
                    else:
                        self.discordBot.guilds[guild.id] = mongoUpdate

                temporary_channel = guild_cache.get('temporary', {}).get('channels', {}).get(f'{voice_channel.id}', '')

                if temporary_channel:
                    if len(members) == 0:
                        # Leaves last member in voice channel
                        query = {f'temporary.channels.{voice_channel.id}': ''}
                        filter = {'id': guild.id}

                        mongoUpdate = self.mongoDataBase.update_field(database_name='dbot', collection_name='guilds', action='$unset', query=query, filter=filter)

                        if mongoUpdate is None:
                            print('Voice channel not deleted from DataBase')
                        else:
                            self.discordBot.guilds[guild.id] = mongoUpdate
                            # del self.discordBot.guilds[guild.id]['temporary']['channels'][f'{voice_channel.id}']

                            await voice_channel.delete()
                    else:
                        if member.bot:
                            return

                        # Leaves not last member in voice channel
                        owner = guild_cache.get('temporary', {}).get('channels', {}).get(f'{voice_channel.id}', {}).get('owner', {})

                        if owner.get('id', '') == member.id:
                            # Leaves owner of voice channel
                            new_owner = None

                            for tmember in members:
                                if not tmember.bot:
                                    new_owner = tmember

                            if not new_owner:
                                return

                            query = {f'temporary.channels.{voice_channel.id}.owner.id': new_owner.id}
                            filter = {'id': guild.id}

                            mongoUpdate = self.mongoDataBase.update_field(database_name='dbot', collection_name='guilds', action='$set',
                                                            query=query, filter=filter)

                            if mongoUpdate is None:
                                print('New owner not added to DataBase')
                            else:
                                self.discordBot.guilds[guild.id] = mongoUpdate
                                # self.discordBot.guilds[guild.id]['temporary']['channels'][f'{voice_channel.id}']['owner']['id'] = new_owner.id

                                await voice_channel.set_permissions(new_owner, overwrite=utils.default_role)
                                await voice_channel.edit(name=f'@{new_owner.name}')


            # User join voice channel
            if after.channel is not None:
                voice_channel = after.channel
                guild = voice_channel.guild

                # Get data from database
                # query = {'_id': 0, 'temporary': 1, 'members': 1}
                # filter = {'id': guild.id}
                # document = self.mongoDataBase.get_document(database_name='dbot', collection_name='guilds', query=query, filter=filter)

                guild_cache = self.discordBot.guilds.get(guild.id, {})
                if not guild_cache:
                    return

                init_channel = guild_cache.get('temporary', {}).get('inits', {}).get(f'{voice_channel.id}', '')

                if init_channel:
                    # overwrites = {
                    #     guild.default_role: utils.default_role,
                    #     guild.me: utils.owner_role,
                    # }

                    if not self.mongoDataBase.check_connection():
                        return

                    category = voice_channel.category

                    if category:
                        voice_channel = await category.create_voice_channel(name=f'@{member.name}', position=voice_channel.position)
                    else:
                        voice_channel = await guild.create_voice_channel(name=f'@{member.name}', position=voice_channel.position)

                    await voice_channel.set_permissions(member, overwrite=utils.default_role)
                    await member.move_to(channel=voice_channel)

                    query = {f'temporary.channels.{voice_channel.id}.owner': {'id': member.id}}
                    filter = {'id': guild.id}

                    mongoUpdate = self.mongoDataBase.update_field(database_name='dbot', collection_name='guilds', action='$set', query=query, filter=filter)

                    if mongoUpdate is None:
                        print('Created voice channel not added to DataBase')
                    else:
                        self.discordBot.guilds[guild.id] = mongoUpdate
                        # self.discordBot.guilds[guild.id]['temporary']['channels'][f'{voice_channel.id}']= {'owner': {'id': member.id}}
                else:
                    # Joined not in init channel
                    date = datetime.now(tz=pytz.utc)
                    date = date.strftime('%Y-%m-%d %H:%M:%S')

                    query = {f'members.{member.id}.stats.joined': date}
                    filter = {'id': guild.id}

                    mongoUpdate = self.mongoDataBase.update_field(database_name='dbot', collection_name='guilds', action='$set',
                                                       query=query, filter=filter)

                    if mongoUpdate is None:
                        print('Not updated joined value of member in DataBase')
                    else:
                        self.discordBot.guilds[guild.id] = mongoUpdate
                        # self.discordBot.guilds[guild.id]['members'][f'{member.id}']['stats']['joined'] = date
        except Exception as e:
            print(e)

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
        query = {f'members.{message.author.id}.stats.messages_count': 1}
        filter = {'id': message.guild.id}

        mongoUpdate = self.mongoDataBase.update_field(database_name='dbot', collection_name='guilds', action='$inc', filter=filter,
                                           query=query)
        if mongoUpdate is None:
            print('Not updated messages count of member in DataBase')
        else:
            self.discordBot.guilds[message.guild.id] = mongoUpdate


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
