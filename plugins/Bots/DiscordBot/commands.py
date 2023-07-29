import json
import aiohttp
import discord
import utils

from plugins.DataBase.mongo import MongoDataBase


class DiscordBotCommand:
    """
    DiscordBot Command
    """

    def __init__(self, mongoDataBase: MongoDataBase = None):
        self.mongoDataBase = mongoDataBase

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
                query = {'_id': 0, 'temporary': 1}
                filter = {'id': guild.id}
                document = self.mongoDataBase.get_document(database_name='dbot', collection_name='guilds', query=query,
                                                           filter=filter)

                if not document:
                    return await webhook.send(f"Something wrong with DataBase")

                owner = document.get('temporary', {}).get('channels', {}).get(f'{voice_channel.id}', {}).get('owner',
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
                query = {'_id': 0, 'temporary': 1}
                filter = {'id': guild.id}
                document = self.mongoDataBase.get_document(database_name='dbot', collection_name='guilds', query=query,
                                                           filter=filter)

                if not document:
                    return await webhook.send(f"Something wrong with DataBase")

                owner = document.get('temporary', {}).get('channels', {}).get(f'{voice_channel.id}', {}).get('owner',
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
                query = {'_id': 0, 'temporary': 1}
                filter = {'id': guild.id}
                document = self.mongoDataBase.get_document(database_name='dbot', collection_name='guilds', query=query,
                                                           filter=filter)

                if not document:
                    return await webhook.send(f"Something wrong with DataBase")

                owner = document.get('temporary', {}).get('channels', {}).get(f'{voice_channel.id}', {}).get('owner',
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
                query = {'_id': 0, 'temporary': 1}
                filter = {'id': guild.id}
                document = self.mongoDataBase.get_document(database_name='dbot', collection_name='guilds', query=query,
                                                           filter=filter)

                if not document:
                    return await webhook.send(f"Something wrong with DataBase")

                owner = document.get('temporary', {}).get('channels', {}).get(f'{voice_channel.id}', {}).get('owner',
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

    async def voice_rename(self, interaction: discord.Interaction, text: str):
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
                query = {'_id': 0, 'temporary': 1}
                filter = {'id': guild.id}
                document = self.mongoDataBase.get_document(database_name='dbot', collection_name='guilds', query=query,
                                                           filter=filter)

                if not document:
                    return await webhook.send(f"Something wrong with DataBase")

                owner = document.get('temporary', {}).get('channels', {}).get(f'{voice_channel.id}', {}).get('owner',
                                                                                                             {})

                if owner:
                    if owner.get('id', '') == user.id:
                        await voice_channel.edit(name=f'voice-{text}')
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
                    voice_channel = await category.create_voice_channel('JOIN to CREATE voice channel')
                else:
                    voice_channel = await guild.create_voice_channel('JOIN to CREATE voice channel')

            query = {'_id': 0, 'temporary': 1}
            filter = {'id': guild.id}
            document = self.mongoDataBase.get_document(database_name='dbot', collection_name='guilds', query=query,
                                                       filter=filter)

            if not document:
                return await webhook.send(f"Something wrong with DataBase")

            temporary_channel = document.get('temporary', {}).get('inits', {}).get(f'{voice_channel.id}', {})

            if temporary_channel:
                query = {f'temporary.inits.{voice_channel.id}': ''}
                filter = {'id': guild.id}

                if self.mongoDataBase.update_field(database_name='dbot', collection_name='guilds', action='$unset',
                                                   query=query, filter=filter) is None:
                    await webhook.send(f"Something wrong with DataBase")
                else:
                    await webhook.send(f"Voice channel <#{voice_channel.id}> is unset")
            else:
                query = {f'temporary.inits.{voice_channel.id}.owner': {'id': user.id}}
                filter = {'id': guild.id}

                if self.mongoDataBase.update_field(database_name='dbot', collection_name='guilds', action='$set',
                                                   query=query, filter=filter) is None:
                    await webhook.send(f"Something wrong with DataBase")
                else:
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
                query = {'_id': 0, 'temporary': 1}
                filter = {'id': guild.id}
                document = self.mongoDataBase.get_document(database_name='dbot', collection_name='guilds', query=query,
                                                           filter=filter)

                if not document:
                    return await webhook.send(f"Something wrong with DataBase")

                owner = document.get('temporary', {}).get('channels', {}).get(f'{voice_channel.id}', {}).get('owner',
                                                                                                             {})

                if owner:
                    if member is not None:
                        if owner.get('id', '') == user.id:
                            await voice_channel.set_permissions(member, overwrite=utils.default_role)

                            query = {f'temporary.channels.{voice_channel.id}.owner.id': member.id}
                            filter = {'id': guild.id}

                            if self.mongoDataBase.update_field(database_name='dbot', collection_name='guilds',
                                                               action='$set',
                                                               query=query, filter=filter) is None:
                                await webhook.send(f"Something wrong with DataBase")
                            else:
                                await webhook.send(f'New owner the {voice_channel.mention} is <@{member.id}> :)')
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
