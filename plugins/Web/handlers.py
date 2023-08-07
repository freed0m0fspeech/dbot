"""
WebServerHandler plugin to work with Handler
"""
import json
import os
from datetime import datetime

from json import dumps, JSONDecodeError

import discord
from bson import json_util
from dotenv import load_dotenv
from aiohttp.web import Response, Request, json_response
from pytz import utc

from plugins.Bots.DiscordBot.handlers import DiscordBotHandler

load_dotenv()

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS').split(' ')


class WebServerHandler:
    """
    Class to work with Handler
    """

    def __init__(self, webServer):
        self.webServer = webServer
        self.mongoDataBase = webServer.mongoDataBase
        self.__register_routes()

        if webServer.discordBot:
            self.discordBot = webServer.discordBot
            self.discordBotHandler = DiscordBotHandler(webSerber=self.webServer, discordBot=self.discordBot,
                                                       mongoDataBase=self.mongoDataBase)
            # self.__register_handlers_discordmBot()

    # ------------------------------------------------------------------------------------------------------------------
    # Register ---------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    # Routes -----------------------------------------------------------------------------------------------------------
    def __register_routes(self):
        self.webServer.client.router.add_route('GET', '/', self.__default_handler)
        self.webServer.client.router.add_route('POST', '/', self.__default_handler)
        self.webServer.client.router.add_route('GET', '/member/{guild_id:[^\\/]+}/{member_id:[^\\/]+}',
                                               self.__member_parameters_handler)
        self.webServer.client.router.add_route('GET', '/user/{user_id:[^\\/]+}', self.__user_parameters_handler)
        self.webServer.client.router.add_route('GET', '/guild/{guild_id:[^\\/]+}', self.__guild_parameters_handler)
        self.webServer.client.router.add_route('POST', '/send/{guild_id:[^\\/]+}/{channel_id:[^\\/]+}',
                                               self.__send_message_handler)
        self.webServer.client.router.add_route('POST', '/manage/{guild_id:[^\\/]+}/{member_id:[^\\/]+}',
                                               self.__manage_guild_handler)

    # Discord ----------------------------------------------------------------------------------------------------------
    def __register_handlers_discordmBot(self):
        pass

    # ------------------------------------------------------------------------------------------------------------------
    # Routes Handler --------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    async def __default_handler(self, request: 'Request'):
        return Response(text="I'm Web handler")

    async def __send_message_handler(self, request: 'Request'):
        if request.headers.get('Origin', '').split("//")[-1].split("/")[0].split('?')[0] not in ALLOWED_HOSTS:
            return Response(status=403)

        guild_id = request.match_info['guild_id']
        channel_id = request.match_info['channel_id']

        try:
            data = await request.json()
        except JSONDecodeError:
            return Response(status=500)

        if not data.get('publicKey', '') == os.getenv('RSA_PUBLIC_KEY', ''):
            return Response(status=403)

        try:
            guild = self.discordBot.client.get_guild(int(guild_id))
        except Exception as e:
            print(e)
            return Response(status=422)

        if not guild or not guild_id or not channel_id:
            return Response(status=422)

        text = data.get('text', '')
        if text:
            await guild.get_channel(int(channel_id)).send(text)

        return Response()

    async def __member_parameters_handler(self, request: 'Request'):
        if request.headers.get('Origin', '').split("//")[-1].split("/")[0].split('?')[0] not in ALLOWED_HOSTS:
            return Response(status=403)

        member_id = request.match_info['member_id']
        guild_id = request.match_info['guild_id']

        try:
            data = await request.json()
        except JSONDecodeError:
            return Response(status=500)

        if not data.get('publicKey', '') == os.getenv('RSA_PUBLIC_KEY', ''):
            return Response(status=403)

        try:
            guild = self.discordBot.client.get_guild(int(guild_id))
            member = guild.get_member(int(member_id))

            date = datetime.now(tz=utc)
            date = date.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(e)
            return Response(status=500)

        if not member or not member_id or not guild_id or not guild:
            return Response(status=422)

        member_parameters = {}
        for attr in [attr for attr in dir(member) if not attr.startswith('_')]:
            try:
                value = getattr(member, attr)
                member_parameters[attr] = json.dumps(value, default=json_util.default)
            except Exception as e:
                # Not serializable
                pass

        member_parameters['date'] = date

        response = {
            'member_parameters': member_parameters,
        }

        return json_response(response)

    async def __user_parameters_handler(self, request: 'Request'):
        if request.headers.get('Origin', '').split("//")[-1].split("/")[0].split('?')[0] not in ALLOWED_HOSTS:
            return Response(status=403)

        user_id = request.match_info['user_id']

        try:
            data = await request.json()

            date = datetime.now(tz=utc)
            date = date.strftime('%Y-%m-%d %H:%M:%S')
        except JSONDecodeError:
            return Response(status=500)

        if not data.get('publicKey', '') == os.getenv('RSA_PUBLIC_KEY', ''):
            return Response(status=403)

        try:
            user = self.discordBot.client.get_user(int(user_id))
        except Exception as e:
            print(e)
            return Response(status=500)

        if not user or not user_id:
            return Response(status=422)

        user_parameters = {}

        for attr in [attr for attr in dir(user) if not attr.startswith('_')]:
            try:
                value = getattr(user, attr)
                user_parameters[attr] = json.dumps(value, default=json_util.default)
            except Exception as e:
                # Not serializable
                pass

        user_parameters['date'] = date

        response = {
            'user_parameters': user_parameters,
        }

        return json_response(response)

    async def __guild_parameters_handler(self, request: 'Request'):
        if request.headers.get('Origin', '').split("//")[-1].split("/")[0].split('?')[0] not in ALLOWED_HOSTS:
            return Response(status=403)

        guild_id = request.match_info['guild_id']

        try:
            data = await request.json()
        except JSONDecodeError:
            return Response(status=500)

        if not data.get('publicKey', '') == os.getenv('RSA_PUBLIC_KEY', ''):
            return Response(status=403)

        try:
            guild = self.discordBot.client.get_guild(int(guild_id))

            query = {'_id': 0, 'discord': 1}
            site_document = self.mongoDataBase.get_document(database_name='site', collection_name='freedom_of_speech',
                                                            query=query)

            if not site_document:
                Response(status=500)

            after = site_document.get('discord', {}).get('guild_parameters', {}).get('date', None)
            after = datetime.strptime(after, '%Y-%m-%d %H:%M:%S')

            messages_count = {}
            for member in site_document.get('discord', {}).get('members_parameters', {}):
                messages_count[member] = site_document.get(member, {}).get('messages_count', 0)

            for text_channel in guild.text_channels:
                text_channel: discord.TextChannel
                # Max 1000 messages to fetch per channel
                async for message in text_channel.history(limit=1000, after=after):
                    try:
                        messages_count[f'{message.author.id}'] += 1
                    except KeyError:
                        messages_count[f'{message.author.id}'] = 1

            date = datetime.now(tz=utc)
            date = date.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(e)
            return Response(status=500)

        if not guild or not guild_id:
            return Response(status=422)

        guild_parameters = {}
        for attr in [attr for attr in dir(guild) if not attr.startswith('_')]:
            value = getattr(guild, attr)

            try:
                guild_parameters[attr] = json.dumps(value, default=json_util.default)
            except Exception as e:
                # Not serializable
                pass

        guild_parameters['date'] = date

        query = {'_id': 0, 'members': 1, 'xp': 1}
        dbot_document = self.mongoDataBase.get_document(database_name='dbot', collection_name='guilds',
                                                        filter={'id': guild.id}, query=query)

        if not dbot_document:
            Response(status=500)

        message_xp = dbot_document.get('xp', {}).get('message_xp', 100)
        voice_xp = dbot_document.get('xp', {}).get('voice_xp', 50)
        xp_factor = dbot_document.get('xp', {}).get('xp_factor', 100)  # threshold

        guild_parameters['message_xp'] = message_xp
        guild_parameters['voice_xp'] = voice_xp
        guild_parameters['xp_factor'] = xp_factor

        members_parameters = {}
        for member in guild.members:
            member_parameters = {}
            for attr in [attr for attr in dir(member) if not attr.startswith('_')]:
                try:
                    value = getattr(member, attr)
                    member_parameters[attr] = json.dumps(value, default=json_util.default)
                except Exception as e:
                    # Not serializable
                    pass

            voicetime = dbot_document.get('members', {}).get(f'{member.id}', {}).get('stats', {}).get('voicetime', 0)
            member_messages_count = messages_count.get(f'{member.id}', 0)
            xp = (member_messages_count * message_xp) + ((voicetime // 60) * voice_xp)

            date = datetime.now(tz=utc)
            date = date.strftime('%Y-%m-%d %H:%M:%S')

            member_parameters['date'] = date
            member_parameters['voicetime'] = voicetime
            member_parameters['xp'] = xp
            members_parameters['messages_count'] = member_messages_count

            members_parameters[f'{member.id}'] = member_parameters

        stats = []

        for member_id, parameters in members_parameters.items():
            stat = (member_id, parameters.get('xp', 0))
            stats.append(stat)

        # Sort members by xp
        stats.sort(reverse=True, key=lambda x: x[1])

        i = 0
        for stat in stats:
            i += 1
            # Position for member in chat by xp
            member_id = stat[0]
            members_parameters[member_id]['position'] = i

        response = {
            'guild_parameters': guild_parameters,
            'members_parameters': members_parameters,
        }

        return json_response(response)

    async def __manage_guild_handler(self, request: 'Request'):
        if request.headers.get('Origin', '').split("//")[-1].split("/")[0].split('?')[0] not in ALLOWED_HOSTS:
            return Response(status=403)

        member_id = request.match_info['member_id']
        guild_id = request.match_info['guild_id']

        try:
            data = await request.json()
        except JSONDecodeError:
            return Response(status=500)

        if not data.get('publicKey', '') == os.getenv('RSA_PUBLIC_KEY', ''):
            return Response(status=403)

        action = data.get('action', '')
        parameters = data.get('parameters', '')

        if not action:
            return Response(status=422)

        try:
            guild = self.discordBot.client.get_guild(int(guild_id))
            member = guild.get_member(int(member_id))
        except Exception as e:
            member = None
            guild = None

        if not member or not guild or not member_id or not guild_id:
            return Response(status=422)

        if action == 'demote_chat_member':
            pass

        if action == 'promote_chat_member':
            pass

        return Response()

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
