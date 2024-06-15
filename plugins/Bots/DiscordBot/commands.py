import asyncio
import datetime
import logging
import re
from random import shuffle

import discord
import pymongo
import pytz

from plugins.DataBase.mongo import MongoDataBase
from plugins.Helpers.logger_filters import YouTubeLogFilter
from utils import cache, AudioSourceTracked, delete_slice, ResultThread
from plugins.Bots.DiscordBot.roles import secret_roles
from collections import deque
from plugins.Helpers.youtube_dl import get_best_info_media, regex_link

max_music_queue_len = 5000

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
    #         if not voice_channel:
    #             return await webhook.send(f"Меня нет в голосовом канале")
    #
    #         if not user_voice:
    #             return await webhook.send(f"Вы не в голосовом канале")
    #
    #         user_voice_channel = user_voice.channel
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

    async def _defer(self, interaction: discord.Interaction, ephemeral: bool = True) -> discord.Webhook:
        response = interaction.response
        response: discord.InteractionResponse
        await response.defer(ephemeral=ephemeral)  # ephemeral - only you can see this

        webhook = interaction.followup
        webhook: discord.Webhook

        return webhook

    async def _check_user_in_voice(self, user: discord.Member, webhook: discord.Webhook):
        user_voice = user.voice
        if not user_voice:
            await webhook.send("Вы не в голосовом канале", ephemeral=True)
            return None

        voice_channel = user_voice.channel
        if not voice_channel:
            await webhook.send("Вы не в голосовом канале", ephemeral=True)
            return None

        return voice_channel

    async def _check_user_owner_of_voice_channel(self, user: discord.Member, guild: discord.Guild, voice_channel: discord.VoiceChannel, webhook: discord.Webhook):
        owner = cache.stats.get(guild.id, {}).get('tvoice_channels', {}).get(voice_channel.id, {}).get('owner', {})

        if not owner:
            await webhook.send('Информация о владельце голосового канала не найдена')
            return None

        if not owner.get('id', '') == user.id:
            await webhook.send('Вы не владелец этого голосового канала')
            return None

        return owner
    async def _check_user_together_with_voice_client(self, guild: discord.Guild, voice_channel:discord.VoiceChannel, webhook: discord.Webhook):
        voice_client = guild.voice_client
        if not voice_client:
            await webhook.send("Меня нет в голосовом канале", ephemeral=True)
            return None

        if not voice_client.channel == voice_channel:
            await webhook.send('Вы находитесь в другом голосовом канале', ephemeral=True)
            return None

        return voice_client

    async def voice_lock(self, interaction: discord.Interaction):
        webhook = await self._defer(interaction)

        try:
            guild = interaction.guild
            user = interaction.user

            voice_channel = await self._check_user_in_voice(user=user, webhook=webhook)
            if not voice_channel:
                return

            owner = await self._check_user_owner_of_voice_channel(user=user, guild=guild, voice_channel=voice_channel, webhook=webhook)
            if not owner:
                return

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
        webhook = await self._defer(interaction)

        try:
            guild = interaction.guild
            user = interaction.user

            voice_channel = await self._check_user_in_voice(user=user, webhook=webhook)
            if not voice_channel:
                return

            owner = await self._check_user_owner_of_voice_channel(user=user, guild=guild, voice_channel=voice_channel,
                                                                  webhook=webhook)
            if not owner:
                return

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
        webhook = await self._defer(interaction)

        try:
            guild = interaction.guild
            user = interaction.user

            voice_channel = await self._check_user_in_voice(user=user, webhook=webhook)
            if not voice_channel:
                return

            owner = await self._check_user_owner_of_voice_channel(user=user, guild=guild, voice_channel=voice_channel, webhook=webhook)
            if not owner:
                return

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
        webhook = await self._defer(interaction)

        try:
            guild = interaction.guild
            user = interaction.user

            voice_channel = await self._check_user_in_voice(user=user, webhook=webhook)
            if not voice_channel:
                return

            owner = await self._check_user_owner_of_voice_channel(user=user, guild=guild, voice_channel=voice_channel,
                                                                  webhook=webhook)
            if not owner:
                return

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
        webhook = await self._defer(interaction)

        try:
            guild = interaction.guild
            user = interaction.user

            voice_channel = await self._check_user_in_voice(user=user, webhook=webhook)
            if not voice_channel:
                return

            owner = await self._check_user_owner_of_voice_channel(user=user, guild=guild, voice_channel=voice_channel, webhook=webhook)
            if not owner:
                return

            await voice_channel.edit(name=f'{text}')
            await webhook.send(f'Голосовой канал {voice_channel.mention} был переименован')
        except Exception as e:
            return await webhook.send(str(e))

    async def voice_init(self, interaction: discord.Interaction, voice_channel: discord.VoiceChannel = None):
        webhook = await self._defer(interaction)

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
        webhook = await self._defer(interaction)

        try:
            guild = interaction.guild
            user = interaction.user

            voice_channel = await self._check_user_in_voice(user=user, webhook=webhook)
            if not voice_channel:
                return

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
        webhook = await self._defer(interaction)

        try:
            guild = interaction.guild
            user = interaction.user

            voice_channel = await self._check_user_in_voice(user=user, webhook=webhook)
            if not voice_channel:
                return

            owner = await self._check_user_owner_of_voice_channel(user=user, guild=guild, voice_channel=voice_channel, webhook=webhook)
            if not owner:
                return

            await voice_channel.edit(user_limit=user_limit)
            await webhook.send(f'Лимит пользователей для голосового канала {voice_channel.mention} изменен на {user_limit}')
        except Exception as e:
            return await webhook.send(str(e))

    async def _play(self, guild, leave: bool = False):
        if not guild.voice_client:
            return

        if len(guild.voice_client.channel.members) == 1:
            return await guild.voice_client.disconnect(force=True)

        music_queue = self.discordBot.music.get(guild.id, {}).get('queue', deque())
        music_queue_len = len(self.discordBot.music.get(guild.id, {}).get('queue', {}))
        max_items = max_music_queue_len - music_queue_len
        max_items += 1

        try:
            music_queue = music_queue.popleft()
            info = music_queue[0]
            user = music_queue[1]
        except IndexError:
            return

        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'ignoreerrors': True,
            'noplaylist': True, # https://www.youtube.com/watch?v=PDjRAJlP3BY&list=PLs6raD4eTyko0Jmuu0O5nAkpt-Tq8DJ3b - example of link that will add playlist (noplaylist true)
            'playliststart': f'1', # https://www.youtube.com/playlist?list=PLgULlLHTSGIQ9BeVZY37fJP50CYc3lkW2 - example of link will add playlist ignoring no playlist
            'playlistend': f'{max_items}',
            # 'skip_download': True,
            'extract_flat': 'in_playlist',
            # 'outtmpl': '/temp/media/%(title)s.%(ext)s', # Change download path
            'logger': YouTubeLogFilter(),
        }

        ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                          'options': f'-vn -loglevel fatal'}

        # if os.path.isdir("temp/media"):
        #     shutil.rmtree("temp/media")

        # Delete previous temp files
        # dirpath = "temp/media"
        # if os.path.isdir(dirpath):
        #     for filename in os.listdir(dirpath):
        #         filepath = os.path.join(dirpath, filename)
        #         # try:
        #         #     shutil.rmtree(filepath)
        #         # except OSError:
        #         try:
        #             os.remove(filepath)
        #         except PermissionError:
        #             continue

        # if os.path.exists(f"{os.getcwd()}/temp"):
        #     shutil.rmtree(f"/temp")

        infoThread = ResultThread(lambda: get_best_info_media(info.get('original_url', info.get('url', '')), ydl_opts))
        infoThread.start()

        while infoThread.is_alive():
            await asyncio.sleep(1)

        # info = results[0]
        info = infoThread.result

        # info = await self.discordBot.client.loop.run_in_executor(None, lambda: get_best_info_media(info.get('original_url', info.get('url', '')), ydl_opts))

        if isinstance(info, list):
            if user:
                # if music_queue_len < len(info):
                for video in reversed(info):
                    self.discordBot.music[guild.id]['queue'].appendleft((video, user))
                # else:
                #     for video in info[0:max_items]:
                #         self.discordBot.music[guild.id]['queue'].appendleft((video.get('url', ''), user))

                return await self._play(guild=guild)

        url = info.get('url', '') if isinstance(info, dict) else ''
        # filepath = info.get('requested_downloads', [])[0].get('filepath', '') if info.get('requested_downloads', []) else ''

        if url:
            audioSource = AudioSourceTracked(discord.FFmpegPCMAudio(url, **ffmpeg_options), path=url)
            # audioSource = AudioSourceTracked(FFmpegPCMAudio(filepath, **ffmpeg_options), path=filepath)
            self.discordBot.audiosource = audioSource

            try:
                if leave:
                    after = None
                else:
                    after = lambda ex: asyncio.run(self._play(guild=guild))

                voice_client = guild.voice_client
                voice_client_is_busy = voice_client.is_playing()

                if voice_client_is_busy and leave:
                    voice_client.pause()

                voice_client.play(self.discordBot.audiosource, after=after)

                self.discordBot.music['now'] = (info, user)
                self.discordBot.music[guild.id]['queue_history'].appendleft((info, user))
            except discord.errors.ClientException:
                return self.discordBot.music[guild.id]['queue'].appendleft(music_queue)
            # await guild.voice_client.connect(reconnect=True, timeout=3000)
            # guild.voice_client.play(FFmpegPCMAudio(filepath, **ffmpeg_options), after=lambda ex: asyncio.run(self._play(guild=guild)))
        else:
            # logging.info('Not found url for music queue item')
            return await self._play(guild=guild)

    async def _music_play_callback(self, interaction: discord.Interaction):
        data: dict = interaction.data

        if data:
            arguments = data.get('custom_id', '').split(' ')

            try:
                url = data.get('values', [])[0]
            except IndexError:
                url = None

            try:
                appendleft = arguments[0] == 'True'
            except IndexError:
                appendleft = None

            try:
                leave = arguments[1] == 'True'
            except IndexError:
                leave = None

            await self.music_play(interaction=interaction, text=url, appendleft=appendleft, leave=leave)

    async def music_play(self, interaction: discord.Interaction, text: str, appendleft: bool = False, result_count: int = 1, leave: bool = False):
        webhook = await self._defer(interaction)

        try:
            guild = interaction.guild
            user = interaction.user

            if isinstance(user, discord.Member):
                await secret_roles(member=user, guild=guild, event='using command /music play')

            if not text:
                return await webhook.send('Текст не найден')

            voice_channel = await self._check_user_in_voice(user=user, webhook=webhook)
            if not voice_channel:
                return

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
                if not voice_client_is_busy or len(voice_client.channel.members) == 1:
                    await voice_client.disconnect(force=True)
                    voice_client = await voice_channel.connect(reconnect=True, timeout=3000)
                    await guild.change_voice_state(channel=voice_channel)
                    # await voice_client.move_to(channel=voice_channel)

                    voice_client_is_busy = False

                    self.discordBot.music[guild.id]['queue_history'] = deque(maxlen=10)
                    self.discordBot.music[guild.id]['queue'] = deque()
                else:
                    return await webhook.send('Кто-то уже использует меня в другом голосовом канале')

            # if playliststart or playlistend:
            #     if not playliststart or not playlistend:
            #         return await webhook.send('Задайте оба параметра start и end')
            #
            #     if playliststart < 0 or playlistend < 0 or playliststart > playlistend:
            #         return await webhook.send('Неверные значения параметров start и end')

            if len(self.discordBot.music.get(guild.id, {}).get('queue', {})) < max_music_queue_len:
                music_queue_len = len(self.discordBot.music.get(guild.id, {}).get('queue', {}))
                max_items = max_music_queue_len - music_queue_len
                max_items += 1

                ydl_opts = {
                    'format': 'bestaudio/best',
                    'quiet': True,
                    'ignoreerrors': True,
                    'noplaylist': True,
                    'playliststart': f'1',
                    'playlistend': f'{max_items}',
                    # 'skip_download': True,
                    'extract_flat': True, # 'in_playlist'
                    # 'outtmpl': '/temp/media/%(title)s.%(ext)s', # Change download path
                    'logger': YouTubeLogFilter(),
                    # 'cachedir': False,
                }

                if re.match(regex_link, text):
                    url = text
                else:
                    url = None

                if result_count < 0:
                    result_count = 1

                # 25 max_value for select in discord
                result_count = min(result_count, 25)

                # info = await self.discordBot.client.loop.run_in_executor(None, lambda: get_best_info_media(text, ydl_opts, result_count=result_count))
                infoThread = ResultThread(lambda: get_best_info_media(text, ydl_opts, result_count=result_count))
                infoThread.start()

                while infoThread.is_alive():
                    await asyncio.sleep(1)

                info = infoThread.result

                if not url and result_count > 1:
                    if isinstance(info, list):
                        results = [(item.get('title', ''), item.get('url', ''), item.get('duration', 0)) for item in info]

                        if not results:
                            return await webhook.send(f"Ничего не найдено по запросу `{text}`")

                        select = discord.ui.Select(options=[discord.SelectOption(label=f"{datetime.timedelta(seconds=round(result[2])) if result[2] else ''} {result[0]}"[:100], value=result[1][:100]) for result in results],
                                                   placeholder='Выбери что добавить', custom_id=f'{appendleft} {leave}')
                        select.callback = self._music_play_callback
                        return await webhook.send(view=discord.ui.View().add_item(select))
                    else:
                        return await webhook.send(f"Ничего не найдено по запросу `{text}`")
                if isinstance(info, dict):
                    if appendleft:
                        self.discordBot.music[guild.id]['queue'].appendleft((info, user))
                    else:
                        self.discordBot.music[guild.id]['queue'].append((info, user))
                    await webhook.send(f"`{info.get('title', '')}` был добавлен в музыкальную очередь")
                elif isinstance(info, list):
                    if user:
                        count = 0

                        if appendleft:
                            info.reverse()

                        for video in info:
                            if video.get('title', '') == '[Deleted video]':
                                continue

                            if appendleft:
                                self.discordBot.music[guild.id]['queue'].appendleft((video, user))
                            else:
                                self.discordBot.music[guild.id]['queue'].append((video, user))
                            count += 1

                        if len(info) == 0:
                            return await webhook.send(f"Ничего не найдено по запросу `{text}`")

                        if len(info) == 1:
                            await webhook.send(f"`{info[0].get('title', '')}` был добавлен в музыкальную очередь")
                        else:
                            await webhook.send(f"`{count}` элементов было добавлено в музыкальную очередь")
            else:
                await webhook.send(f'Достигнута максимальная длина музыкальной очереди')

            if result_count > 1:
                await interaction.delete_original_response()

            if not voice_client_is_busy or leave:
                return await self._play(guild=guild, leave=leave)
        except Exception as e:
            return await webhook.send(str(e))

    async def music_seek(self, interaction: discord.Interaction, time: str):
        webhook = await self._defer(interaction)

        try:
            guild = interaction.guild
            user = interaction.user

            voice_channel = await self._check_user_in_voice(user=user, webhook=webhook)
            if not voice_channel:
                return

            voice_client = await self._check_user_together_with_voice_client(guild=guild, voice_channel=voice_channel, webhook=webhook)
            if not voice_client:
                return

            if not voice_client.is_playing() and not voice_client.is_paused():
                return await webhook.send('Ничего не воспроизводится', ephemeral=True)

            dtime = datetime.datetime.strptime(f"{time}", "%H:%M:%S")
            dtimedelta = datetime.timedelta(hours=dtime.hour, minutes=dtime.minute, seconds=dtime.second)

            now = self.discordBot.music.get('now', [{}, None])
            info = now[0]
            duration = round(info.get('duration', 0))
            if duration > 600:
                return await webhook.send('Возможно перемотать только песню длительность которой менее 10 минут', ephemeral=True)

            if duration < dtimedelta.seconds:
                return await webhook.send('Длительность песни меньше перематываемого значения', ephemeral=True)

            ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                              'options': f'-vn -loglevel fatal -ss {dtimedelta.seconds}'}
            # ffmpeg_options = {'options': f'-vn -loglevel fatal -ss {dtimedelta.seconds}'}

            path = self.discordBot.audiosource.path
            audioSource = AudioSourceTracked(discord.FFmpegPCMAudio(path, **ffmpeg_options), path, dtimedelta.seconds)
            self.discordBot.audiosource = audioSource

            if voice_client.is_playing():
                voice_client.pause()

            voice_client.play(self.discordBot.audiosource, after=lambda ex: asyncio.run(self._play(guild=guild)))

            return await webhook.send(f'Текущая песня перемотана на {dtimedelta}', ephemeral=True)
        except Exception as e:
            return await webhook.send(str(e))

    async def _music_repeat(self, interaction: discord.Interaction):
        webhook = await self._defer(interaction)

        try:
            guild = interaction.guild
            user = interaction.user

            voice_channel = await self._check_user_in_voice(user=user, webhook=webhook)
            if not voice_channel:
                return

            voice_client = await self._check_user_together_with_voice_client(guild=guild, voice_channel=voice_channel, webhook=webhook)
            if not voice_client:
                return

            if not voice_client.is_playing() and not voice_client.is_paused():
                return await webhook.send('Ничего не воспроизводится', ephemeral=True)

            audioSource = self.discordBot.audiosource
            ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                              'options': f'-vn -loglevel fatal'}
            audioSource = AudioSourceTracked(discord.FFmpegPCMAudio(audioSource.path, **ffmpeg_options), path=audioSource.path)
            self.discordBot.audiosource = audioSource

            if voice_client.is_playing():
                voice_client.pause()

            voice_client.play(self.discordBot.audiosource, after=lambda ex: repeat())

            def repeat():
                audioSource = self.discordBot.audiosource
                ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                                  'options': f'-vn -loglevel fatal'}
                audioSource = AudioSourceTracked(discord.FFmpegPCMAudio(audioSource.path, **ffmpeg_options), path=audioSource.path)
                self.discordBot.audiosource = audioSource
                voice_client.play(self.discordBot.audiosource, after=lambda ex: repeat())

            return await webhook.send(f'Текущая песня поставлена на повтор', ephemeral=True)
        except Exception as e:
            return await webhook.send(str(e), ephemeral=True)

    async def music_queue(self, interaction: discord.Interaction):
        webhook = await self._defer(interaction)

        try:
            guild = interaction.guild
            user = interaction.user

            voice_channel = await self._check_user_in_voice(user=user, webhook=webhook)
            if not voice_channel:
                return

            voice_client = await self._check_user_together_with_voice_client(guild=guild, voice_channel=voice_channel, webhook=webhook)
            if not voice_client:
                return

            music_queue = self.discordBot.music.get(guild.id, {}).get('queue', deque())

            if not music_queue:
                return await webhook.send(f"Музыкальная очередь пуста")

            # content = f"Музыкальная очередь ({guild.name}) - {len(music_queue)} total:\n\n"
            content = ''

            # music_queue = [f'`{queue[0]}` added by {queue[1].display_name}\n' for queue in music_queue][0:20]
            # First 20 queue items
            for i in range(0, 20):
                try:
                    music = music_queue[i]
                    info = music[0]
                    user = music[1]

                    # try:
                    #     playliststart = music[2]
                    #     playlistend = music[3]
                    # except IndexError:
                    #     playliststart = None
                    #     playlistend = None
                except Exception as e:
                    break

                user: discord.Member

                # if playliststart and playlistend:
                #     content = f'{content}{i}. `{title}` **{playliststart} - {playlistend}** добавил(а) {user.mention}\n'
                # else:
                content = f"{content}{i}. `{info.get('title', info.get('url', '')) if isinstance(info, dict) else info}` добавил(а) {user.mention}\n"

            queue_embed = discord.Embed(title=f"Музыкальная очередь ({guild.name}) - {len(music_queue)}",
                                        description=f"{content}",
                                        color=discord.Color.random(),
                                        timestamp=datetime.datetime.now(tz=pytz.timezone('Europe/Kiev')))
            queue_embed.set_author(name=guild.name, icon_url=guild.icon)
            queue_embed.set_thumbnail(url=guild.icon)

            return await webhook.send(embed=queue_embed)
        except Exception as e:
            return await webhook.send(str(e))

    async def _music_history(self, interaction: discord.Interaction):
        webhook = await self._defer(interaction)

        try:
            guild = interaction.guild
            user = interaction.user

            voice_channel = await self._check_user_in_voice(user=user, webhook=webhook)
            if not voice_channel:
                return

            voice_client = await self._check_user_together_with_voice_client(guild=guild, voice_channel=voice_channel, webhook=webhook)
            if not voice_client:
                return

            music_queue_history = self.discordBot.music.get(guild.id, {}).get('queue_history', deque())

            if not music_queue_history:
                return await webhook.send(f"История музыкальной очереди пуста")

            content = ''
            # First 20 queue items
            for i in range(0, 10):
                try:
                    music = music_queue_history[i]
                    info = music[0]
                    user = music[1]
                except Exception as e:
                    break

                user: discord.Member
                content = f"{content}{i}. `{info.get('title', '')}` добавил(а) {user.mention}\n"

            queue_embed = discord.Embed(title=f"История музыкальной очереди ({guild.name}) - {len(music_queue_history)}",
                                        description=f"{content}",
                                        color=discord.Color.random(),
                                        timestamp=datetime.datetime.now(tz=pytz.timezone('Europe/Kiev')))
            queue_embed.set_author(name=guild.name, icon_url=guild.icon)
            queue_embed.set_thumbnail(url=guild.icon)

            return await webhook.send(embed=queue_embed)
        except Exception as e:
            return await webhook.send(str(e))

    async def music_shuffle(self, interaction: discord.Interaction):
        webhook = await self._defer(interaction)

        try:
            guild = interaction.guild
            user = interaction.user

            voice_channel = await self._check_user_in_voice(user=user, webhook=webhook)
            if not voice_channel:
                return

            voice_client = await self._check_user_together_with_voice_client(guild=guild, voice_channel=voice_channel, webhook=webhook)
            if not voice_client:
                return

            music_queue = self.discordBot.music.get(guild.id, {}).get('queue', deque())
            if not music_queue:
                return await webhook.send(f"Музыкальная очередь пуста")

            shuffle(music_queue)
            self.discordBot.music[guild.id]['queue'] = music_queue

            return await webhook.send('Музыкальная очередь была перемешана')
        except Exception as e:
            return await webhook.send(str(e))

    async def music_reverse(self, interaction: discord.Interaction):
        webhook = await self._defer(interaction)

        try:
            guild = interaction.guild
            user = interaction.user

            voice_channel = await self._check_user_in_voice(user=user, webhook=webhook)
            if not voice_channel:
                return

            voice_client = await self._check_user_together_with_voice_client(guild=guild, voice_channel=voice_channel, webhook=webhook)
            if not voice_client:
                return

            music_queue = self.discordBot.music.get(guild.id, {}).get('queue', deque())
            if not music_queue:
                return await webhook.send(f"Музыкальная очередь пуста")

            music_queue.reverse()
            self.discordBot.music[guild.id]['queue'] = music_queue

            return await webhook.send('Музыкальная очередь была перевернута')
        except Exception as e:
            return await webhook.send(str(e))

    async def music_skip(self, interaction: discord.Interaction):
        webhook = await self._defer(interaction)

        try:
            guild = interaction.guild
            user = interaction.user
            custom_id = interaction.data.get('custom_id', '')

            voice_channel = await self._check_user_in_voice(user=user, webhook=webhook)
            if not voice_channel:
                return

            voice_client = await self._check_user_together_with_voice_client(guild=guild, voice_channel=voice_channel, webhook=webhook)
            if not voice_client:
                return

            if len(self.discordBot.music.get(guild.id, {}).get('queue', deque())) == 0:
                return await webhook.send('Нет следующей песни', ephemeral=True)

            if voice_client.is_playing() or voice_client.is_paused():
                voice_client.stop()
                if len(self.discordBot.music.get(guild.id, {}).get('queue', deque())) == 0:
                    return await webhook.send('Нет следующей песни', ephemeral=True)
                else:
                    if not custom_id:
                        return await webhook.send(content='Воспроизведение следующей песни', ephemeral=True)
        except Exception as e:
            logging.warning(e)
            return await webhook.send(content=str(e), ephemeral=True)

    async def music_pause(self, interaction: discord.Interaction):
        webhook = await self._defer(interaction)

        try:
            guild = interaction.guild
            user = interaction.user
            custom_id = interaction.data.get('custom_id', '')

            voice_channel = await self._check_user_in_voice(user=user, webhook=webhook)
            if not voice_channel:
                return

            voice_client = await self._check_user_together_with_voice_client(guild=guild, voice_channel=voice_channel, webhook=webhook)
            if not voice_client:
                return

            if voice_client.is_playing():
                voice_client.pause()

                if not custom_id:
                    await webhook.send('Воспроизведение песни приостановлено', ephemeral=True)
            elif voice_client.is_paused():
                voice_client.resume()

                if not custom_id:
                    await webhook.send('Воспроизведение песни возобновлено', ephemeral=True)
            else:
                return await webhook.send('Ничего не воспроизводится', ephemeral=True)
        except Exception as e:
            logging.warning(e)
            return await webhook.send(str(e), ephemeral=True)

    async def music_clear(self, interaction: discord.Interaction, count: int = None, start: int = None):
        webhook = await self._defer(interaction)

        try:
            guild = interaction.guild
            user = interaction.user

            voice_channel = await self._check_user_in_voice(user=user, webhook=webhook)
            if not voice_channel:
                return

            voice_client = await self._check_user_together_with_voice_client(guild=guild, voice_channel=voice_channel, webhook=webhook)
            if not voice_client:
                return

            if not count:
                self.discordBot.music[guild.id]['queue'].clear()
                return await webhook.send('Музыкальная очередь полностью очищена')

            if start and start > 0:
                start_index = start - 1
                if count > 0:
                    delete_slice(self.discordBot.music[guild.id]['queue'], start=start_index, stop=start_index + count)

                    return await webhook.send(f'{count} запрос(ов) удалено начиная с {start} позиции музыкальной очереди')
            else:
                if count > 0:
                    for _ in range(count):
                        self.discordBot.music[guild.id]['queue'].popleft()
                    return await webhook.send(f'{count} запрос(ов) удалено в начале музыкальной очереди')
                else:
                    for _ in range(abs(count)):
                        self.discordBot.music[guild.id]['queue'].pop()
                    return await webhook.send(f'{abs(count)} запрос(ов) удалено в конце музыкальной очереди')
        except IndexError:
            return await webhook.send('Музыкальная очередь пуста')
        except Exception as e:
            return await webhook.send(str(e))

    async def music_previous(self, interaction: discord.Interaction):
        webhook = await self._defer(interaction)

        try:
            guild = interaction.guild
            user = interaction.user
            custom_id = interaction.data.get('custom_id', '')

            voice_channel = await self._check_user_in_voice(user=user, webhook=webhook)
            if not voice_channel:
                return

            voice_client = await self._check_user_together_with_voice_client(guild=guild, voice_channel=voice_channel, webhook=webhook)
            if not voice_client:
                return

            now_playing = None
            if voice_client.is_playing() or voice_client.is_paused():
                try:
                    now_playing = self.discordBot.music[guild.id].get('queue_history', deque()).popleft()
                except IndexError:
                    now_playing = None

            try:
                previous_info = self.discordBot.music[guild.id].get('queue_history', deque()).popleft()
            except IndexError:
                if now_playing is not None:
                    self.discordBot.music[guild.id]['queue_history'].appendleft(now_playing)

                return await webhook.send('Нет предыдущей песни', ephemeral=True)

            ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                              'options': f'-vn -loglevel fatal'}

            info = previous_info[0]
            user = previous_info[1]

            url = info.get('original_url', '') if isinstance(info, dict) else ''

            if url:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'quiet': True,
                    'ignoreerrors': True,
                    'noplaylist': True,
                    # https://www.youtube.com/watch?v=PDjRAJlP3BY&list=PLs6raD4eTyko0Jmuu0O5nAkpt-Tq8DJ3b - example of link that will add playlist (noplaylist true)
                    'playliststart': f'1',
                    # https://www.youtube.com/playlist?list=PLgULlLHTSGIQ9BeVZY37fJP50CYc3lkW2 - example of link will add playlist ignoring no playlist
                    'playlistend': f'1',
                    # 'skip_download': True,
                    # 'extract_flat': 'in_playlist',
                    # 'outtmpl': '/temp/media/%(title)s.%(ext)s', # Change download path
                    'logger': YouTubeLogFilter(),
                }

                infoThread = ResultThread(lambda: get_best_info_media(url, ydl_opts))
                infoThread.start()

                while infoThread.is_alive():
                    await asyncio.sleep(1)

                # info = results[0]
                info = infoThread.result

                # info = await self.discordBot.client.loop.run_in_executor(None, lambda: get_best_info_media(url, ydl_opts))

                url = info.get('url', '') if isinstance(info, dict) else ''

                if url:
                    audioSource = AudioSourceTracked(discord.FFmpegPCMAudio(url, **ffmpeg_options), path=url)
                    self.discordBot.audiosource = audioSource

                    if voice_client.is_playing():
                        voice_client.pause()

                    guild.voice_client.play(self.discordBot.audiosource, after=lambda ex: asyncio.run(self._play(guild=guild)))
                    self.discordBot.music['now'] = (info, user)

                    self.discordBot.music[guild.id]['queue_history'].appendleft(previous_info)

                    if now_playing is not None:
                        self.discordBot.music[guild.id]['queue'].appendleft(now_playing)

                    if not custom_id:
                        return await webhook.send('Воспроизведение предыдущей песни', ephemeral=True)
            else:
                return await self._play(guild=guild)
        except Exception as e:
            logging.warning(e)
            return await webhook.send(str(e), ephemeral=True)

    async def music_now(self, interaction: discord.Interaction):
        webhook = await self._defer(interaction)

        try:
            guild = interaction.guild
            user = interaction.user

            voice_channel = await self._check_user_in_voice(user=user, webhook=webhook)
            if not voice_channel:
                return

            voice_client = await self._check_user_together_with_voice_client(guild=guild, voice_channel=voice_channel, webhook=webhook)
            if not voice_client:
                return

            if not voice_client.is_playing() and not voice_client.is_paused():
                return await webhook.send('Ничего не воспроизводится')

            now = self.discordBot.music.get('now', [{}, None])
            info = now[0]
            user = now[1]

            uploader = info.get('uploader', '')
            uploader_url = info.get('uploader_url', '')

            if uploader and uploader_url:
                description = f"[{uploader}]({uploader_url})"
            else:
                description = ''

            now_embed = discord.Embed(title=f"{info.get('title', 'Неизвестная песня')}",
                                      description=description,
                                      color=discord.Color.random(),
                                      timestamp=datetime.datetime.now(tz=pytz.timezone('Europe/Kiev')),
                                      url=info.get('webpage_url', ''))
            now_embed.add_field(name='Добавил(а)',
                                value=f"{user.mention}",
                                inline=False)

            percent: float = round(self.discordBot.audiosource.progress / info.get('duration', 1), 1)
            progress_bar = ''
            for i in range(11):
                if percent == round(i / 10, 1):
                    progress_bar += '♡'
                else:
                    progress_bar += '─'

            now_embed.add_field(name='Прогресс', value=f"{progress_bar}", inline=False)
            now_embed.add_field(name='Длительность',
                                value=f"{datetime.timedelta(seconds=round(self.discordBot.audiosource.progress))} | {datetime.timedelta(seconds=round(info.get('duration', 0)))}",
                                inline=False)
            # now_embed.set_author(icon_url=client.user.avatar.url, name="Now playing")

            thumbnail_url = info.get('thumbnails', [{}])[-1].get('url', '')
            now_embed.set_thumbnail(url=thumbnail_url)
            now_embed.set_author(name=guild.name, icon_url=guild.icon)

            view = discord.ui.View(timeout=None)

            # button = discord.ui.Button(label='↺', style=discord.ButtonStyle.primary)
            # button.callback = self.music_repeat
            # view.add_item(button)

            # button = discord.ui.Button(label='𝄞', style=discord.ButtonStyle.primary)
            # button.callback = self.music_queue
            # view.add_item(button)

            button = discord.ui.Button(label='|◁', style=discord.ButtonStyle.primary)
            button.callback = self.music_previous
            view.add_item(button)

            button = discord.ui.Button(label='II', style=discord.ButtonStyle.primary)
            button.callback = self.music_pause
            view.add_item(button)

            button = discord.ui.Button(label='▷|', style=discord.ButtonStyle.primary)
            button.callback = self.music_skip
            view.add_item(button)

            # button = discord.ui.TextInput(label='Перемотать музыку', placeholder='hh:mm:ss')
            # button.callback = self.music_seek
            # view.add_item(button)

            return await webhook.send(embed=now_embed, view=view)
        except Exception as e:
            return await webhook.send(str(e))

    async def music_stop(self, interaction: discord.Interaction):
        webhook = await self._defer(interaction)

        try:
            guild = interaction.guild
            user = interaction.user

            voice_channel = await self._check_user_in_voice(user=user, webhook=webhook)
            if not voice_channel:
                return

            voice_client = await self._check_user_together_with_voice_client(guild=guild, voice_channel=voice_channel,
                                                                             webhook=webhook)
            if not voice_client:
                return

            # if not voice_client.is_playing() and not voice_client.is_paused():
            #     return await webhook.send('Ничего не воспроизводится')

            await voice_client.disconnect(force=True)
            return await webhook.send('Воспроизведение музыки остановлено')
        except Exception as e:
            return await webhook.send(str(e))

    async def music_lyrics(self, interaction: discord.Interaction, text: str = None):
        webhook = await self._defer(interaction)

        try:
            guild = interaction.guild
            user = interaction.user

            if not text:
                voice_channel = await self._check_user_in_voice(user=user, webhook=webhook)
                if not voice_channel:
                    return

                voice_client = await self._check_user_together_with_voice_client(guild=guild, voice_channel=voice_channel, webhook=webhook)
                if not voice_client:
                    return

                if not voice_client.is_playing() and not voice_client.is_paused():
                    return await webhook.send('Ничего не воспроизводится')

                now = self.discordBot.music.get('now', [{}])
                info = now[0]
                lyrics = await self.discordBot.google.lyrics(song_name=f"{info.get('title', '')} lyrics")

                if not lyrics:
                    return await webhook.send('Текст песни не найден')

                content = f"[{lyrics.get('title', '')}]({lyrics.get('link', '')}):\n{lyrics.get('lyrics', '')}"
                # max length for discord
                content = f"{content[:1998]}.." if len(content) > 2000 else content

                return await webhook.send(content)
            else:
                lyrics = await self.discordBot.google.lyrics(song_name=f"{text} lyrics")

                if not lyrics:
                    return await webhook.send('Текст песни не найден')

                content = f"[{lyrics.get('title', '')}]({lyrics.get('link', '')}):\n{lyrics.get('lyrics', '')}"
                # max length for discord
                content = f"{content[:1998]}.." if len(content) > 2000 else content

                return await webhook.send(content)
        except Exception as e:
            return await webhook.send(str(e))
