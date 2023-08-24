"""
Web plugin to work with Web
"""
import asyncio
import gettext
import os

from aiohttp import web
from plugins.Bots.DiscordBot.bot import DiscordBot
from plugins.Web.handlers import WebServerHandler
from plugins.DataBase.mongo import MongoDataBase
from plugins.Google.google import Google


class WebServer:
    """
    Class to work with Handler
    """

    def __init__(self, mongoDataBase: MongoDataBase = None, discordBot: DiscordBot = None, google: Google = None):
        self.mongoDataBase = mongoDataBase

        self.discordBot = discordBot
        self.google = google
        self.client = web.Application()

        self.handler = WebServerHandler(webServer=self)
        self.client.on_startup.append(self.__on_startup)
        self.client.on_shutdown.append(self.__on_shutdown)

    async def __on_startup(self, web):
        pass

    async def __on_shutdown(self, web):
        pass
