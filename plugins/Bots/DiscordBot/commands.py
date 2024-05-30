import asyncio
import json
import logging
import math
import datetime
import random

import aiohttp
import discord
import pymongo
import pytz

import plugins.Helpers.youtube_dl
import utils

from discord import FFmpegPCMAudio, FFmpegOpusAudio
from plugins.DataBase.mongo import MongoDataBase
from plugins.Helpers.logger_filters import YouTubeLogFilter
from utils import cache
from plugins.Bots.DiscordBot.roles import secret_roles


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

    # async def bot_leave(self, interaction: discord.Interaction):
    #     response = interaction.response
    #     response: discord.InteractionResponse
    #     await response.defer(ephemeral=True)  # ephemeral - only you can see this
    #
    #     webhook = interaction.followup
    #     webhook: discord.Webhook
    #
    #     try:
    #         user = interaction.user
    #         guild = interaction.guild
    #         voice_client = guild.voice_client
    #         user_voice = user.voice
    #
    #         if not voice_client:
    #             return await webhook.send(f"Меня нет в голосовом канале")
    #
    #         voice_channel = voice_client.channel
    #
    #         if not voice_channel:
    #             return await webhook.send(f"Меня нет в голосовом канале")
    #
    #         if not user_voice:
    #             return await webhook.send(f"Вы не в голосовом канале")
    #
    #         user_voice_channel = user_voice.channel
    #
    #         if not user_voice_channel:
    #             return await webhook.send(f"Вы не в голосовом канале")
    #
    #         if not user_voice_channel == voice_channel:
    #             return await webhook.send(f"Команда может быть использована только в голосовом канале с ботом")
    #
    #         owner = cache.stats.get(guild.id, {}).get('tvoice_channels', {}).get(voice_channel.id, {}).get('owner', {})
    #
    #         if not owner:
    #             return await webhook.send('Информация о владельце голосового канала не найдена')
    #
    #         if not owner.get('id', '') == user.id:
    #             return await webhook.send('Вы не владелец голосового канала')
    #
    #         await voice_client.disconnect()
    #         return await webhook.send('Спасибо, что выгнали меня')
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

            if not voice_channel:
                return await webhook.send('Вы не в голосовом канале')

            owner = cache.stats.get(guild.id, {}).get('tvoice_channels', {}).get(voice_channel.id, {}).get('owner', {})

            if not owner:
                return await webhook.send('Информация о владельце голосового канала не найдена')

            if not owner.get('id', '') == user.id:
                return await webhook.send('Вы не владелец этого голосового канала')

            overwrites = voice_channel.overwrites_for(guild.default_role)

            if overwrites.is_empty() or overwrites.view_channel:
                overwrites.update(view_channel=False)
                # overwrites.view_channel = True
                await webhook.send('Голосовой канал закрыт')
            else:
                # overwrites.view_channel = False
                overwrites.update(view_channel=True)
                await webhook.send('Голосовой канал открыт')

            await voice_channel.set_permissions(guild.default_role, overwrite=overwrites, reason='Lock')
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

            if not voice_channel:
                return await webhook.send('Вы не в голосовом канале')

            owner = cache.stats.get(guild.id, {}).get('tvoice_channels', {}).get(voice_channel.id, {}).get('owner', {})

            if not owner:
                return await webhook.send('Информация о владельце голосового канала не найдена')

            if not owner.get('id', '') == user.id:
                return await webhook.send('Вы не владелец этого голосового канала')

            overwrites = voice_channel.overwrites_for(role)

            if overwrites.view_channel:
                overwrites = None
                await webhook.send(f'<@&{role.id}> кикнут(а) с голосового канала')
            else:
                overwrites.update(view_channel=True)
                await webhook.send(f'<@&{role.id}> приглашен(а) в голосовой канал')

            await voice_channel.set_permissions(role, overwrite=overwrites, reason='Invite')
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

            if not voice_channel:
                return await webhook.send('Вы не в голосовом канале')

            owner = cache.stats.get(guild.id, {}).get('tvoice_channels', {}).get(voice_channel.id, {}).get('owner', {})

            if not owner:
                return await webhook.send('Информация о владельце голосового канала не найдена')

            if not owner.get('id', '') == user.id:
                return await webhook.send('Вы не владелец этого голосового канала')

            member_voice = member.voice

            if not member_voice:
                return await webhook.send('Участник не в вашем голосовом канале')

            if not member_voice.channel == voice_channel:
                return await webhook.send('Участник не в вашем голосовом канале')

            await member.edit(voice_channel=None)
            await webhook.send(f'<@{member.id}> отключен от голосового канала')
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

            if not voice_channel:
                return await webhook.send('Вы не в голосовом канале')

            owner = cache.stats.get(guild.id, {}).get('tvoice_channels', {}).get(voice_channel.id, {}).get('owner', {})

            if not owner:
                return await webhook.send('Информация о владельце голосового канала не найдена')

            if not owner.get('id', '') == user.id:
                return await webhook.send('Вы не владелец этого голосового канала')

            overwrites = voice_channel.overwrites_for(member)

            if overwrites.view_channel:
                overwrites = None
                await webhook.send(f'<@{member.id}> кикнут(а) с голосового канала')
            else:
                overwrites.update(view_channel=True)
                await webhook.send(f'<@{member.id}> приглашен(а) в голосовой канал')

            await voice_channel.set_permissions(member, overwrite=overwrites, reason='Invite')
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

            if not voice_channel:
                return await webhook.send('Вы не в голосовом канале')

            owner = cache.stats.get(guild.id, {}).get('tvoice_channels', {}).get(voice_channel.id, {}).get('owner', {})

            if not owner:
                return await webhook.send('Информация о владельце голосового канала не найдена')

            if not owner.get('id', '') == user.id:
                return await webhook.send('Вы не владелец этого голосового канала')

            await voice_channel.edit(name=f'{text}')
            await webhook.send(f'Голосовой канал {voice_channel.mention} был переименован')
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
                return await webhook.send(f"Эта команда может быть использована только владельцем сервера")

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
                return await webhook.send(f"Что-то не так с базой данных")

            temporary_channel = self.discordBot.guilds.get(guild.id, {}).get('temporary', {}).get('inits', {}).get(
                f'{voice_channel.id}', {})

            if temporary_channel:
                query = {f'temporary.inits.{voice_channel.id}': ''}
                filter = {'id': guild.id}

                with pymongo.timeout(0.3):
                    mongoUpdate = self.mongoDataBase.update_field(database_name='dbot', collection_name='guilds',
                                                                  action='$unset',
                                                                  query=query, filter=filter)

                if mongoUpdate is None:
                    await webhook.send(f"Что-то не так с базой данных")
                else:
                    self.discordBot.guilds[guild.id] = mongoUpdate
                    await webhook.send(f"Голосовой канал <#{voice_channel.id}> снят")
            else:
                query = {f'temporary.inits.{voice_channel.id}.owner': {'id': user.id}}
                filter = {'id': guild.id}

                with pymongo.timeout(0.3):
                    mongoUpdate = self.mongoDataBase.update_field(database_name='dbot', collection_name='guilds',
                                                                  action='$set',
                                                                  query=query, filter=filter)

                if mongoUpdate is None:
                    await webhook.send(f"Что-то не так с базой данных")
                else:
                    # self.discordBot.guilds[guild.id]['temporary']['inits'][f'{voice_channel.id}'] = {'owner': {'id': user.id}}
                    self.discordBot.guilds[guild.id] = mongoUpdate
                    await webhook.send(f"Голосовой канал <#{voice_channel.id}> установлен")
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

            if not voice_channel:
                return await webhook.send('Вы не в голосовом канале')

            owner = cache.stats.get(guild.id, {}).get('tvoice_channels', {}).get(voice_channel.id, {}).get('owner', {})

            if not owner:
                return await webhook.send('Информация о владельце голосового канала не найдена')

            if member is not None:
                if not owner.get('id', '') == user.id:
                    return await webhook.send('Вы не владелец этого голосового канала')

                overwrites = voice_channel.overwrites
                overwrites[member] = discord.PermissionOverwrite.from_pair(allow=discord.Permissions.all_channel(),
                                                                           deny=discord.Permissions.none())
                del overwrites[user]

                await voice_channel.edit(name=f'@{member.name}', overwrites=overwrites)

                await webhook.send(f'Новый владелец голосового канала {voice_channel.mention}: <@{member.id}> :)')

                cache.stats[guild.id]['tvoice_channels'][voice_channel.id]['owner']['id'] = member.id
            else:
                await webhook.send(f"Владелец голосового канала {voice_channel.mention}: <@{owner.get('id', '')}>")
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

            if not voice_channel:
                return await webhook.send('Вы не в голосовом канале')

            owner = cache.stats.get(guild.id, {}).get('tvoice_channels', {}).get(voice_channel.id, {}).get('owner', {})

            if not owner:
                return await webhook.send('Информация о владельце голосового канала не найдена')

            if not owner.get('id', '') == user.id:
                return await webhook.send('Вы не владелец этого голосового канала')

            await voice_channel.edit(user_limit=user_limit)
            await webhook.send(
                f'Лимит пользователей для голосового канала {voice_channel.mention} изменен на {user_limit}')
        except Exception as e:
            return await webhook.send(str(e))

    async def _play(self, guild):
        if not guild.voice_client:
            return

        if guild.voice_client.channel.members == 1:
            return await guild.voice_client.voice_disconnect()

        music_queue = self.discordBot.music.get(guild.id, {}).get('queue', [])

        try:
            music_queue = music_queue.pop(0)
            title = music_queue[0]
            user = music_queue[1]
        except Exception:
            # return await guild.voice_client.voice_disconnect()
            return

        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'ignoreerrors': True,
            'noplaylist': True, # https://www.youtube.com/watch?v=PDjRAJlP3BY&list=PLs6raD4eTyko0Jmuu0O5nAkpt-Tq8DJ3b example of link that will add playlist (noplaylist true)
            'playliststart': '1', # https://www.youtube.com/playlist?list=PLgULlLHTSGIQ9BeVZY37fJP50CYc3lkW2 - example of link will add playlist ignoring no playlist
            'playlistend': '20',
            # 'skip_download': True,
            'extract_flat': 'in_playlist',
            'logger': YouTubeLogFilter(),
        }

        ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                          'options': '-vn -loglevel warning'}

        info = await plugins.Helpers.youtube_dl.get_best_info_media(title=title, ydl_opts=ydl_opts)

        if isinstance(info, list):
            if user:
                for video in info:
                    self.discordBot.music[guild.id]['queue'].append((video.get('url', ''), user))

                return await self._play(guild=guild)

        self.discordBot.music['now'] = (info, user)

        url = info.get('url', '')

        if url:
            # await guild.voice_client.connect(reconnect=True, timeout=3000)

            guild.voice_client.play(FFmpegPCMAudio(url, **ffmpeg_options),
                                    after=lambda ex: asyncio.run(self._play(guild=guild)))
        else:
            return await self._play(guild=guild)
    async def music_play(self, interaction: discord.Interaction, text: str):
        response = interaction.response
        response: discord.InteractionResponse
        await response.defer(ephemeral=True)  # ephemeral - only you can see this

        webhook = interaction.followup
        webhook: discord.Webhook

        try:
            guild = interaction.guild
            user = interaction.user

            if isinstance(user, discord.Member):
                await secret_roles(member=user, guild=guild, event='using command /music play')

            try:
                voice_channel = user.voice.channel
            except Exception:
                voice_channel = None

            if not voice_channel:
                return await webhook.send('Вы не в голосовом канале')

            voice_client = guild.voice_client
            voice_client: discord.VoiceClient

            if not voice_client:
                voice_client = await voice_channel.connect(reconnect=True, timeout=3000)
                await guild.change_voice_state(channel=voice_channel)
            else:
                if not voice_client.is_connected():
                    voice_client = await voice_channel.connect(reconnect=True, timeout=3000)
                    await guild.change_voice_state(channel=voice_channel)

            voice_client_is_busy = voice_client.is_playing()  # or voice_client.is_paused()

            if not voice_client.channel.id == voice_channel.id:
                if not voice_client_is_busy:
                    await voice_client.disconnect(force=True)
                    voice_client = await voice_channel.connect(reconnect=True, timeout=3000)
                    await guild.change_voice_state(channel=voice_channel)
                    # await voice_client.move_to(channel=voice_channel)
                else:
                    return await webhook.send('Кто-то уже использует меня в другом голосовом канале')

            if len(self.discordBot.music.get(guild.id, {}).get('queue', {})) < 20:
                self.discordBot.music[guild.id]['queue'].append((text, user))
                await webhook.send(f'Запрос `{text}` был добавлен в очередь')
            else:
                await webhook.send(f'Максимальная длина музыкальной очереди 20 элементов')

            if not voice_client_is_busy:
                return await self._play(guild=guild)
        except Exception as e:
            return await webhook.send(str(e))

    async def music_queue(self, interaction: discord.Interaction):
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

            try:
                voice_client_channel = guild.voice_client.channel
            except Exception:
                voice_client_channel = None

            if not voice_channel:
                return await webhook.send('Вы не в голосовом канале')

            if voice_client_channel:
                if not voice_client_channel == voice_channel:
                    return await webhook.send('Вы находитесь в другом голосовом канале')

            music_queue = self.discordBot.music.get(guild.id, {}).get('queue', {})

            if not music_queue:
                return await webhook.send(f"Музыкальная очередь пуста")

            # content = f"Музыкальная очередь ({guild.name}) - {len(music_queue)} total:\n\n"
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

                user: discord.Member

                content = f'{content}{i}. `{title}` добавил(а) {user.mention}\n'

            queue_embed = discord.Embed(title=f"Музыкальная очередь ({guild.name}) - {len(music_queue)}",
                                        description=f"{content}",
                                        color=discord.Color.random(),
                                        timestamp=datetime.datetime.now(tz=pytz.timezone('Europe/Kiev')))
            queue_embed.set_author(name=guild.name, icon_url=guild.icon)
            queue_embed.set_thumbnail(url=guild.icon)

            return await webhook.send(embed=queue_embed)
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

            user_voice = user.voice

            if not user_voice:
                return await webhook.send("Вы не в голосовом канале")

            voice_channel = user.voice.channel

            if not voice_channel:
                return await webhook.send("Вы не в голосовом канале")

            voice_client = guild.voice_client

            if not voice_client:
                return await webhook.send("Меня нет в голосовом канале")

            if not voice_client.channel == voice_channel:
                return await webhook.send('Вы находитесь в другом голосовом канале')

            if voice_client.is_playing():  # or voice_client.is_paused()
                voice_client.stop()
                return await webhook.send('Музыка пропущена')

            return await webhook.send('Ничего не воспроизводится')

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

            if not voice_client.channel == voice_channel:
                return await webhook.send('Вы находитесь в другом голосовом канале')

            if count == 0:
                self.discordBot.music[guild.id]['queue'] = []
                return await webhook.send('Музыкальная очередь полностью очищена')

            if count > 0:
                for _ in range(count):
                    self.discordBot.music[guild.id]['queue'].pop(0)
                return await webhook.send(f'{count} запрос(ов) удалено с начала музыкальной очереди')
            else:
                for _ in range(abs(count)):
                    self.discordBot.music[guild.id]['queue'].pop()
                return await webhook.send(f'{abs(count)} запрос(ов) удалено с конца музыкальной очереди')
        except Exception as e:
            return await webhook.send(str(e))

    async def music_now(self, interaction: discord.Interaction):
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

            if not voice_client.channel == voice_channel:
                return await webhook.send('Вы находитесь в другом голосовом канале')

            if not voice_client.is_playing():  # and not voice_client.is_paused()
                return await webhook.send('Ничего не воспроизводится')

            now = self.discordBot.music.get('now', {})
            info = now[0]
            user = now[1]

            now_embed = discord.Embed(title=f"{info['title']}",
                                      description=f"[{info['channel']}]({info['channel_url']})",
                                      color=discord.Color.random(),
                                      timestamp=datetime.datetime.now(tz=pytz.timezone('Europe/Kiev')),
                                      url=info['webpage_url'])
            now_embed.add_field(name='Добавил(а)',
                                value=f"{user.mention}",
                                inline=True)
            now_embed.add_field(name='Длительность',
                                value=f"{datetime.timedelta(seconds=info['duration'])}",
                                inline=True)
            # now_embed.set_author(icon_url=client.user.avatar.url, name="Now playing")
            thumbnail_url = info['thumbnails'][len(info['thumbnails']) - 1]['url']
            now_embed.set_thumbnail(url=thumbnail_url)
            now_embed.set_author(name=guild.name, icon_url=guild.icon)

            return await webhook.send(embed=now_embed)
        except Exception as e:
            return await webhook.send(str(e))

    async def music_lyrics(self, interaction: discord.Interaction, text: str = None):
        response = interaction.response
        response: discord.InteractionResponse
        await response.defer(ephemeral=True)  # ephemeral - only you can see this

        webhook = interaction.followup
        webhook: discord.Webhook

        try:
            guild = interaction.guild
            user = interaction.user

            if not text:
                voice_channel = user.voice.channel
                voice_client = guild.voice_client

                if not voice_client.channel == voice_channel:
                    return await webhook.send('Вы находитесь в другом голосовом канале')

                if not voice_client.is_playing():  # and not voice_client.is_paused()
                    return await webhook.send('Ничего не воспроизводится')

                now = self.discordBot.music.get('now', {})
                info = now[0]
                lyrics = self.discordBot.google.lyrics(song_name=f"{info['title']} lyrics")

                if not lyrics:
                    return await webhook.send('Текст песни не найден')

                content = f"[{lyrics['title']}]({lyrics['link']}):\n{lyrics['lyrics']}"
                # max length for discord
                content = f"{content[:1998]}.." if len(content) > 2000 else content

                return await webhook.send(content)
            else:
                lyrics = self.discordBot.google.lyrics(song_name=f"{text} lyrics")

                if not lyrics:
                    return await webhook.send('Текст песни не найден')

                content = f"[{lyrics['title']}]({lyrics['link']}):\n{lyrics['lyrics']}"
                # max length for discord
                content = f"{content[:1998]}.." if len(content) > 2000 else content

                return await webhook.send(content)
        except Exception as e:
            return await webhook.send(str(e))
