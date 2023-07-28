"""
WebServerHandler plugin to work with Handler
"""
import asyncio
import json
import os
import textwrap
import rsa
import discord

from discord.ext.commands import command
from json import dumps, JSONDecodeError
from math import sqrt
from bson import json_util
from dotenv import load_dotenv
from aiohttp.web import Response, Request, json_response
from plugins.Bots.DiscordBot.handlers import DiscordBotHandler
from pyrogram.types import ChatPrivileges

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
            self.discordBotHandler = DiscordBotHandler(webSerber=self.webServer, discordBot=self.discordBot, mongoDataBase=self.mongoDataBase)
            # self.__register_handlers_discordmBot()

    # ------------------------------------------------------------------------------------------------------------------
    # Register ---------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    # Routes -----------------------------------------------------------------------------------------------------------
    def __register_routes(self):
        self.webServer.client.router.add_route('GET', '/', self.__default_handler)
        self.webServer.client.router.add_route('POST', '/', self.__default_handler)
        self.webServer.client.router.add_route('GET', '/member/{guild_id:[^\\/]+}/{member_id:[^\\/]+}', self.__member_parameters_handler)
        self.webServer.client.router.add_route('GET', '/user_id/{user_id:[^\\/]+}', self.__user_parameters_handler)
        self.webServer.client.router.add_route('GET', '/guild_id/{guild_id:[^\\/]+}', self.__guild_parameters_handler)
        self.webServer.client.router.add_route('POST', '/send/{guild_id:[^\\/]+}/{channel_id:[^\\/]+}', self.__send_message_handler)
        self.webServer.client.router.add_route('POST', '/manage/{guild_id:[^\\/]+}/{user:[^\\/]+}', self.__manage_guild_handler)

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
            guild = self.discordBot.client.get_guild(guild_id)
        except Exception as e:
            print(e)
            guild = None

        if not guild or not guild_id or not channel_id:
            return Response(status=422)

        text = data.get('text', '')
        if text:
            await guild.get_channel(channel_id).send(text)

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
            member = self.discordBot.client.get_guild(guild_id).get_member(member_id)
        except Exception as e:
            print(e)
            member = None

        if not member or not member_id or not guild_id:
            return Response(status=422)

        member_parameters = {}

        for attr in [attr for attr in dir(member) if not attr.startswith('_')]:
            value = getattr(member, attr)

            try:
                member_parameters[attr] = json.dumps(value, default=json_util.default)
            except Exception as e:
                # Not serializable
                pass

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
        except JSONDecodeError:
            return Response(status=500)

        if not data.get('publicKey', '') == os.getenv('RSA_PUBLIC_KEY', ''):
            return Response(status=403)

        try:
            user = self.discordBot.client.get_user(user_id)
        except Exception as e:
            print(e)
            user = None

        if not user or not user_id:
            return Response(status=422)

        user_parameters = {}

        for attr in [attr for attr in dir(user) if not attr.startswith('_')]:
            value = getattr(user, attr)

            try:
                user_parameters[attr] = json.dumps(value, default=json_util.default)
            except Exception as e:
                # Not serializable
                pass

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
            guild = self.discordBot.client.get_guild(guild_id)
        except Exception as e:
            print(e)
            guild = None

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

        response = {
            'guild_parameters': guild_parameters,
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
            guild = self.discordBot.client.get_guild(guild_id)
            member = guild.get_member(member_id)
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
