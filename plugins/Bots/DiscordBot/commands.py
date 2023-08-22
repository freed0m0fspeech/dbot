import asyncio
import json
import math
import datetime
import random

import aiohttp
import discord
import pytz

import plugins.Helpers.youtube_dl
import utils

from discord import FFmpegPCMAudio
from plugins.DataBase.mongo import MongoDataBase


class DiscordBotCommand:
    """
    DiscordBot Command
    """

    def __init__(self, discordBot, mongoDataBase: MongoDataBase = None):
        self.mongoDataBase = mongoDataBase
        self.discordBot = discordBot

    # ------------------------------------------------------------------------------------------------------------------
    # SLASH COMMANDS ---------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    # async def bot_help(self, interaction: discord.Interaction):
    #     response = interaction.response
    #     response: discord.InteractionResponse
    #     await response.defer(ephemeral=True)  # ephemeral - only you can see this
    #
    #     webhook = interaction.followup
    #     webhook: discord.Webhook
    #
    #     try:
    #         await webhook.send('Helping')
    #     except Exception as e:
    #         return await webhook.send(str(e))
    #
    # async def bot_join(self, interaction: discord.Interaction):
    #     response = interaction.response
    #     response: discord.InteractionResponse
    #     await response.defer(ephemeral=True)  # ephemeral - only you can see this
    #
    #     webhook = interaction.followup
    #     webhook: discord.Webhook
    #
    #     try:
    #         voice_client = interaction.guild.voice_client
    #
    #         if voice_client:
    #             voice_channel = voice_client.channel
    #             voice_channel: discord.VoiceChannel
    #
    #             for member in voice_channel.members:
    #                 if not member.bot:
    #                     return await webhook.send(f"I'm already with someone in voice channel")
    #
    #         voice_state = interaction.user.voice
    #
    #         if voice_state:
    #             await voice_state.channel.connect(reconnect=False, timeout=10000)
    #         else:
    #             return await webhook.send(f"Connect to voice channel to use this command")
    #
    #         return await webhook.send("Wassup homie?")
    #     except Exception as e:
    #         return await webhook.send(str(e))
    #
    # async def bot_leave(self, interaction: discord.Interaction):
    #     response = interaction.response
    #     response: discord.InteractionResponse
    #     await response.defer(ephemeral=True)  # ephemeral - only you can see this
    #
    #     webhook = interaction.followup
    #     webhook: discord.Webhook
    #
    #     try:
    #         guild = interaction.guild
    #         voice_client = guild.voice_client
    #
    #         if not interaction.user.id == guild.owner_id:
    #             return await webhook.send(f"Command can only be used by owner of the server")
    #
    #         if not voice_client:
    #             return
    #
    #         await voice_client.disconnect()
    #         await webhook.send('Thank you for kicking me out')
    #
    #     except Exception as e:
    #         return await webhook.send(str(e))

    # async def fun_quote(self, interaction: discord.Interaction):
    #     response = interaction.response
    #     response: discord.InteractionResponse
    #     await response.defer(ephemeral=True)  # ephemeral - only you can see this
    #
    #     webhook = interaction.followup
    #     webhook: discord.Webhook
    #
    #     try:
    #         async with aiohttp.ClientSession() as session:
    #             async with session.get('https://zenquotes.io/api/random') as web_response:
    #                 if web_response.status == 200:
    #                     json_text = await web_response.text()
    #                     json_data = json.loads(json_text)
    #                     quote_text = json_data[0]['q'] + ' (' + json_data[0]['a'] + ')'
    #
    #                     await webhook.send(f'{quote_text}')
    #                 else:
    #                     await webhook.send('Quote API not working properly')
    #     except Exception as e:
    #         return await webhook.send(str(e))

    # async def server_members(self, interaction: discord.Interaction):
    #     response = interaction.response
    #     response: discord.InteractionResponse
    #     await response.defer(ephemeral=True)  # ephemeral - only you can see this
    #
    #     webhook = interaction.followup
    #     webhook: discord.Webhook
    #
    #     try:
    #         guild = interaction.guild
    #         await webhook.send(f"{guild.member_count} members in {guild}")
    #     except Exception as e:
    #         return await webhook.send(str(e))

    async def voice_lock(self, interaction: discord.Interaction):
        response = interaction.response
        response: discord.InteractionResponse
        await response.defer(ephemeral=True)  # ephemeral - only you can see this

        webhook = interaction.followup
        webhook: discord.Webhook

        try:
            guild = interaction.guild
            user = interaction.user

            try:
                voice_channel = user.voice.channel
            except Exception:
                voice_channel = None

            if voice_channel:
                # query = {'_id': 0, 'temporary': 1}
                # filter = {'id': guild.id}
                # document = self.mongoDataBase.get_document(database_name='dbot', collection_name='guilds', query=query,
                #                                            filter=filter)

                if not self.discordBot.guilds:
                    return await webhook.send(f"Something wrong with DataBase")

                owner = self.discordBot.guilds.get(guild.id, {}).get('temporary', {}).get('channels', {}).get(
                    f'{voice_channel.id}', {}).get('owner',
                                                   {})

                if owner:
                    if owner.get('id', '') == user.id:
                        overwrites = voice_channel.overwrites_for(guild.default_role)
                        if not overwrites.view_channel:
                            overwrites.view_channel = True
                            await webhook.send('Voice channel unlocked')
                        else:
                            overwrites.view_channel = False
                            await webhook.send('Voice channel locked')

                        await voice_channel.set_permissions(guild.default_role, overwrite=overwrites, reason='Lock')

                    else:
                        await webhook.send('You are not voice channel owner')
                else:
                    await webhook.send('No information about voice channel owner found')
            else:
                await webhook.send('You are not in voice channel')
        except Exception as e:
            return await webhook.send(str(e))

    async def voice_role(self, interaction: discord.Interaction, role: discord.Role):
        response = interaction.response
        response: discord.InteractionResponse
        await response.defer(ephemeral=True)  # ephemeral - only you can see this

        webhook = interaction.followup
        webhook: discord.Webhook

        try:
            guild = interaction.guild
            user = interaction.user

            try:
                voice_channel = user.voice.channel
            except Exception:
                voice_channel = None

            if voice_channel:
                # query = {'_id': 0, 'temporary': 1}
                # filter = {'id': guild.id}
                # document = self.mongoDataBase.get_document(database_name='dbot', collection_name='guilds', query=query,
                #                                            filter=filter)

                if not self.discordBot.guilds:
                    return await webhook.send(f"Something wrong with DataBase")

                owner = self.discordBot.guilds.get(guild.id, {}).get('temporary', {}).get('channels', {}).get(
                    f'{voice_channel.id}', {}).get('owner',
                                                   {})

                if owner:
                    if owner.get('id', '') == user.id:
                        overwrites = voice_channel.overwrites_for(role)

                        if overwrites.view_channel:
                            overwrites = None
                            await webhook.send(f'<@&{role.id}> kicked from voice channel')
                        else:
                            overwrites.view_channel = True
                            await webhook.send(f'<@&{role.id}> invited to voice channel')

                        await voice_channel.set_permissions(role, overwrite=overwrites, reason='Invite')

                    else:
                        await webhook.send('You are not voice channel owner')
                else:
                    await webhook.send('No information about voice channel owner found')
            else:
                await webhook.send('You are not in voice channel')
        except Exception as e:
            return await webhook.send(str(e))

    async def voice_disconnect(self, interaction: discord.Interaction, member: discord.Member):
        response = interaction.response
        response: discord.InteractionResponse
        await response.defer(ephemeral=True)  # ephemeral - only you can see this

        webhook = interaction.followup
        webhook: discord.Webhook

        try:
            guild = interaction.guild
            user = interaction.user

            try:
                voice_channel = user.voice.channel
            except Exception:
                voice_channel = None

            if voice_channel:
                # query = {'_id': 0, 'temporary': 1}
                # filter = {'id': guild.id}
                # document = self.mongoDataBase.get_document(database_name='dbot', collection_name='guilds', query=query,
                #                                            filter=filter)

                if not self.discordBot.guilds:
                    return await webhook.send(f"Something wrong with DataBase")

                owner = self.discordBot.guilds.get(guild.id, {}).get('temporary', {}).get('channels', {}).get(
                    f'{voice_channel.id}', {}).get('owner',
                                                   {})

                if owner:
                    if owner.get('id', '') == user.id:

                        member_voice = member.voice

                        if member_voice:
                            if member_voice.channel == voice_channel:
                                await member.edit(voice_channel=None)
                                await webhook.send(f'<@{member.id}> disconnected from voice channel')
                            else:
                                await webhook.send('Member is not in your voice channel')
                        else:
                            await webhook.send('Member is not in voice channel')
                    else:
                        await webhook.send('You are not voice channel owner')
                else:
                    await webhook.send('No information about voice channel owner found')
            else:
                await webhook.send('You are not in voice channel')
        except Exception as e:
            return await webhook.send(str(e))

    async def voice_member(self, interaction: discord.Interaction, member: discord.Member):
        response = interaction.response
        response: discord.InteractionResponse
        await response.defer(ephemeral=True)  # ephemeral - only you can see this

        webhook = interaction.followup
        webhook: discord.Webhook

        try:
            guild = interaction.guild
            user = interaction.user

            try:
                voice_channel = user.voice.channel
            except Exception:
                voice_channel = None

            if voice_channel:
                # query = {'_id': 0, 'temporary': 1}
                # filter = {'id': guild.id}
                # document = self.mongoDataBase.get_document(database_name='dbot', collection_name='guilds', query=query,
                #                                            filter=filter)

                if not self.discordBot.guilds:
                    return await webhook.send(f"Something wrong with DataBase")

                owner = self.discordBot.guilds.get(guild.id, {}).get('temporary', {}).get('channels', {}).get(
                    f'{voice_channel.id}', {}).get('owner',
                                                   {})

                if owner:
                    if owner.get('id', '') == user.id:
                        overwrites = voice_channel.overwrites_for(member)

                        if overwrites.view_channel:
                            overwrites = None
                            await webhook.send(f'<@{member.id}> kicked from voice channel')
                        else:
                            overwrites.view_channel = True
                            await webhook.send(f'<@{member.id}> invited to voice channel')

                        await voice_channel.set_permissions(member, overwrite=overwrites, reason='Invite')

                    else:
                        await webhook.send('You are not voice channel owner')
                else:
                    await webhook.send('No information about voice channel owner found')
            else:
                await webhook.send('You are not in voice channel')
        except Exception as e:
            return await webhook.send(str(e))

    async def voice_name(self, interaction: discord.Interaction, text: str):
        response = interaction.response
        response: discord.InteractionResponse
        await response.defer(ephemeral=True)  # ephemeral - only you can see this

        webhook = interaction.followup
        webhook: discord.Webhook

        try:
            guild = interaction.guild
            user = interaction.user

            try:
                voice_channel = user.voice.channel
            except Exception:
                voice_channel = None

            if voice_channel:
                # query = {'_id': 0, 'temporary': 1}
                # filter = {'id': guild.id}
                # document = self.mongoDataBase.get_document(database_name='dbot', collection_name='guilds', query=query,
                #                                            filter=filter)

                if not self.discordBot.guilds:
                    return await webhook.send(f"Something wrong with DataBase")

                owner = self.discordBot.guilds.get(guild.id, {}).get('temporary', {}).get('channels', {}).get(
                    f'{voice_channel.id}', {}).get('owner',
                                                   {})

                if owner:
                    if owner.get('id', '') == user.id:
                        await voice_channel.edit(name=f'{text}')
                        await webhook.send(f'Voice channel {voice_channel.mention} renamed')
                    else:
                        await webhook.send('You are not voice channel owner')
                else:
                    await webhook.send('No information about voice channel owner found')
            else:
                await webhook.send('You are not in voice channel')
        except Exception as e:
            return await webhook.send(str(e))

    async def voice_init(self, interaction: discord.Interaction, voice_channel: discord.VoiceChannel = None):
        response = interaction.response
        response: discord.InteractionResponse
        await response.defer(ephemeral=True)  # ephemeral - only you can see this

        webhook = interaction.followup
        webhook: discord.Webhook

        try:
            guild = interaction.guild
            user = interaction.user
            if not interaction.user.id == guild.owner_id:
                return await webhook.send(f"This command can only be used by owner of the server")

            if voice_channel is None:
                category = interaction.channel.category

                if category:
                    voice_channel = await category.create_voice_channel(name='JOIN to CREATE')
                else:
                    voice_channel = await guild.create_voice_channel(name='JOIN to CREATE')

            # query = {'_id': 0, 'temporary': 1}
            # filter = {'id': guild.id}
            # document = self.mongoDataBase.get_document(database_name='dbot', collection_name='guilds', query=query,
            #                                            filter=filter)

            if not self.discordBot.guilds:
                return await webhook.send(f"Something wrong with DataBase")

            temporary_channel = self.discordBot.guilds.get(guild.id, {}).get('temporary', {}).get('inits', {}).get(
                f'{voice_channel.id}', {})

            if temporary_channel:
                query = {f'temporary.inits.{voice_channel.id}': ''}
                filter = {'id': guild.id}

                mongoUpdate = self.mongoDataBase.update_field(database_name='dbot', collection_name='guilds',
                                                              action='$unset',
                                                              query=query, filter=filter)

                if mongoUpdate is None:
                    await webhook.send(f"Something wrong with DataBase")
                else:
                    self.discordBot.guilds[guild.id] = mongoUpdate
                    await webhook.send(f"Voice channel <#{voice_channel.id}> is unset")
            else:
                query = {f'temporary.inits.{voice_channel.id}.owner': {'id': user.id}}
                filter = {'id': guild.id}

                mongoUpdate = self.mongoDataBase.update_field(database_name='dbot', collection_name='guilds',
                                                              action='$set',
                                                              query=query, filter=filter)

                if mongoUpdate is None:
                    await webhook.send(f"Something wrong with DataBase")
                else:
                    # self.discordBot.guilds[guild.id]['temporary']['inits'][f'{voice_channel.id}'] = {'owner': {'id': user.id}}
                    self.discordBot.guilds[guild.id] = mongoUpdate
                    await webhook.send(f"Voice channel <#{voice_channel.id}> is set")
        except Exception as e:
            return await webhook.send(str(e))

    async def voice_owner(self, interaction: discord.Interaction, member: discord.Member = None):
        response = interaction.response
        response: discord.InteractionResponse
        await response.defer(ephemeral=True)  # ephemeral - only you can see this

        webhook = interaction.followup
        webhook: discord.Webhook

        try:
            guild = interaction.guild
            user = interaction.user

            try:
                voice_channel = user.voice.channel
            except Exception:
                voice_channel = None

            if voice_channel:
                # query = {'_id': 0, 'temporary': 1}
                # filter = {'id': guild.id}
                # document = self.mongoDataBase.get_document(database_name='dbot', collection_name='guilds', query=query,
                #                                            filter=filter)

                if not self.discordBot.guilds:
                    return await webhook.send(f"Something wrong with DataBase")

                owner = self.discordBot.guilds.get(guild.id, {}).get('temporary', {}).get('channels', {}).get(
                    f'{voice_channel.id}', {}).get('owner',
                                                   {})

                if owner:
                    if member is not None:
                        if owner.get('id', '') == user.id:
                            await voice_channel.set_permissions(member, overwrite=utils.default_role)
                            await voice_channel.edit(name=f'@{member.name}')

                            query = {f'temporary.channels.{voice_channel.id}.owner.id': member.id}
                            filter = {'id': guild.id}

                            mongoUpdate = self.mongoDataBase.update_field(database_name='dbot',
                                                                          collection_name='guilds',
                                                                          action='$set',
                                                                          query=query, filter=filter)
                            if mongoUpdate is None:
                                await webhook.send(f"Something wrong with DataBase")
                            else:
                                # self.discordBot.guilds[guild.id]['temporary']['channels'][f'{voice_channel.id}'] = {'owner': {'id': member.id}}
                                self.discordBot.guilds[guild.id] = mongoUpdate
                                await webhook.send(f'New owner of the {voice_channel.mention} is <@{member.id}> :)')
                        else:
                            await webhook.send('You are not voice channel owner')
                    else:
                        await webhook.send(f"Owner of the {voice_channel.mention} is <@{owner.get('id', '')}>")
                else:
                    await webhook.send('No information about voice channel owner found')
            else:
                await webhook.send('You are not in voice channel')
        except Exception as e:
            return await webhook.send(str(e))

    async def voice_limit(self, interaction: discord.Interaction, user_limit: int):
        response = interaction.response
        response: discord.InteractionResponse
        await response.defer(ephemeral=True)  # ephemeral - only you can see this

        webhook = interaction.followup
        webhook: discord.Webhook

        try:
            guild = interaction.guild
            user = interaction.user

            try:
                voice_channel = user.voice.channel
            except Exception:
                voice_channel = None

            if voice_channel:
                # query = {'_id': 0, 'temporary': 1}
                # filter = {'id': guild.id}
                # document = self.mongoDataBase.get_document(database_name='dbot', collection_name='guilds', query=query,
                #                                            filter=filter)

                if not self.discordBot.guilds:
                    return await webhook.send(f"Something wrong with DataBase")

                owner = self.discordBot.guilds.get(guild.id, {}).get('temporary', {}).get('channels', {}).get(
                    f'{voice_channel.id}', {}).get('owner',
                                                   {})

                if owner:
                    if owner.get('id', '') == user.id:
                        await voice_channel.edit(user_limit=user_limit)
                        await webhook.send(f'Voice channel {voice_channel.mention} user limit chaned to {user_limit}')
                    else:
                        await webhook.send('You are not voice channel owner')
                else:
                    await webhook.send('No information about voice channel owner found')
            else:
                await webhook.send('You are not in voice channel')
        except Exception as e:
            return await webhook.send(str(e))

    async def _play(self, guild):
        if not guild.voice_client:
            return

        if guild.voice_client.channel.members == 1:
            return await guild.voice_client.voice_disconnect()

        music_queue = self.discordBot.music.get(guild.id, {}).get('queue', [])

        try:
            title = music_queue.pop(0)[0]
        except Exception:
            return await guild.voice_client.voice_disconnect()

        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'ignoreerrors': True,
            'noplaylist': True,
        }

        ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                          'options': '-vn'}

        info = await plugins.Helpers.youtube_dl.get_best_info_media(title=title, ydl_opts=ydl_opts)

        if isinstance(info, list):
            info = info[0]

        self.discordBot.music['now'] = info

        url = info.get('url', '')

        guild.voice_client.play(FFmpegPCMAudio(url, **ffmpeg_options),
                          after=lambda ex: asyncio.run(self._play(guild=guild)))

    async def music_play(self, interaction: discord.Interaction, text: str):
        response = interaction.response
        response: discord.InteractionResponse
        await response.defer(ephemeral=True)  # ephemeral - only you can see this

        webhook = interaction.followup
        webhook: discord.Webhook

        try:
            guild = interaction.guild
            user = interaction.user

            # Unique role for using this command (1 in 1.000)
            if round(random.random(), 3) == 0.001:
                if not discord.utils.get(user.roles, name='🎵Диджей'):
                    role = discord.utils.get(guild.roles, name='🎵Диджей')

                    if not role:
                        role = await guild.create_role(name='🎵Диджей', color=discord.Color.dark_orange(),
                                                       hoist=True)
                    await user.add_roles(role)

            try:
                voice_channel = user.voice.channel
            except Exception:
                voice_channel = None

            if voice_channel:
                voice_client = guild.voice_client
                voice_client: discord.VoiceClient

                if not voice_client:
                    voice_client = await voice_channel.connect(reconnect=True, timeout=3000)
                    await guild.change_voice_state(channel=voice_channel)
                else:
                    if not voice_client.is_connected():
                        voice_client = await voice_client.connect(reconnect=True, timeout=3000)
                        await guild.change_voice_state(channel=voice_channel)

                voice_client_is_busy = voice_client.is_playing() or voice_client.is_paused()

                if not voice_client_is_busy:
                    await voice_client.move_to(channel=voice_channel)

                if voice_client.channel.id == voice_channel.id:
                    if len(self.discordBot.music.get(guild.id, {}).get('queue', {})) < 20:
                        self.discordBot.music[guild.id]['queue'].append((text, user))
                        await webhook.send(f'`{text}` added to music queue')
                    else:
                        await webhook.send(f'Music queue max length is 20 items')
                else:
                    return await webhook.send('Someone already using me in another voice channel')

                if not voice_client_is_busy:
                    return await self._play(guild=guild)
            else:
                await webhook.send('You are not in voice channel')
        except Exception as e:
            return await webhook.send(str(e))

    async def music_queue(self, interaction: discord.Interaction):
        response = interaction.response
        response: discord.InteractionResponse
        await response.defer(ephemeral=True)  # ephemeral - only you can see this

        webhook = interaction.followup
        webhook: discord.Webhook

        try:
            client = interaction.client
            guild = interaction.guild
            user = interaction.user

            try:
                voice_channel = user.voice.channel
            except Exception:
                voice_channel = None

            if voice_channel:
                music_queue = self.discordBot.music.get(guild.id, {}).get('queue', {})

                if not music_queue:
                    return await webhook.send(f"Music queue is empty")
                else:
                    # content = f"Music queue ({guild.name}) - {len(music_queue)} total:\n\n"
                    content = ''

                    # music_queue = [f'`{queue[0]}` added by {queue[1].display_name}\n' for queue in music_queue][0:20]
                    # First 20 queue items
                    for i in range(0, 20):
                        try:
                            music = music_queue[i]
                            title = music[0]
                            user = music[1]
                        except Exception as e:
                            break

                        user: discord.User

                        content = f'{content}{i}. `{title}` added by {user.mention}\n'

                    queue_embed = discord.Embed(title=f"Music queue ({guild.name}) - {len(music_queue)} total",
                                              description=f"{content}",
                                              color=discord.Color.random(),
                                              timestamp=datetime.datetime.now(tz=pytz.timezone('Europe/Kiev')))

                    return await webhook.send(embed=queue_embed)
            else:
                await webhook.send('You are not in voice channel')
        except Exception as e:
            return await webhook.send(str(e))

    async def music_skip(self, interaction: discord.Interaction):
        response = interaction.response
        response: discord.InteractionResponse
        await response.defer(ephemeral=True)  # ephemeral - only you can see this

        webhook = interaction.followup
        webhook: discord.Webhook

        try:
            guild = interaction.guild
            user = interaction.user

            voice_channel = user.voice.channel
            voice_client = guild.voice_client

            if voice_client.channel == voice_channel:
                if voice_client.is_paused() or voice_client.is_playing():
                    voice_client.stop()
                    return await webhook.send('Music skipped')
                else:
                    return await webhook.send('Not playing')
            else:
                return await webhook.send('You are not in the same voice channel')

        except Exception as e:
            return await webhook.send(str(e))

    async def music_clear(self, interaction: discord.Interaction, count: int):
        response = interaction.response
        response: discord.InteractionResponse
        await response.defer(ephemeral=True)  # ephemeral - only you can see this

        webhook = interaction.followup
        webhook: discord.Webhook

        try:
            guild = interaction.guild
            user = interaction.user

            voice_channel = user.voice.channel
            voice_client = guild.voice_client

            if voice_client.channel == voice_channel:
                if count == 0:
                    self.discordBot.music[guild.id]['queue'] = []
                    return await webhook.send('Music queue cleared')

                if count > 0:
                    for _ in range(count):
                        self.discordBot.music[guild.id]['queue'].pop(0)
                    return await webhook.send(f'{count} items deleted from start of music queue')
                else:
                    for _ in range(abs(count)):
                        self.discordBot.music[guild.id]['queue'].pop()
                    return await webhook.send(f'{abs(count)} items deleted from end of music queue')
            else:
                return await webhook.send('You are not in the same voice channel')
        except Exception as e:
            return await webhook.send(str(e))

    async def music_now(self, interaction: discord.Interaction):
        response = interaction.response
        response: discord.InteractionResponse
        await response.defer(ephemeral=True)  # ephemeral - only you can see this

        webhook = interaction.followup
        webhook: discord.Webhook

        try:
            client = self.discordBot.client
            guild = interaction.guild
            user = interaction.user

            voice_channel = user.voice.channel
            voice_client = guild.voice_client

            if voice_client.channel == voice_channel:
                if voice_client.is_paused() or voice_client.is_playing():
                    info = self.discordBot.music.get('now', {})

                    now_embed = discord.Embed(title=f"{info['title']}",
                                                      description=f"[{info['channel']}]({info['channel_url']})",
                                                      color=discord.Color.random(),
                                                      timestamp=datetime.datetime.now(tz=pytz.timezone('Europe/Kiev')),
                                                      url=info['webpage_url'])
                    now_embed.add_field(name='Duration',
                                        value=f"{datetime.timedelta(seconds=info['duration'])}",
                                        inline=True)
                    # now_embed.set_author(icon_url=client.user.avatar.url, name="Now playing")
                    thumbnail_url = info['thumbnails'][len(info['thumbnails']) - 1]['url']
                    now_embed.set_thumbnail(url=thumbnail_url)

                    return await webhook.send(embed=now_embed)
                else:
                    return await webhook.send('Not playing')
            else:
                return await webhook.send('You are not in the same voice channel')

        except Exception as e:
            return await webhook.send(str(e))
