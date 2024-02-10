import asyncio
import os

import discord
from aiohttp.web import AppRunner, TCPSite
from dotenv import load_dotenv
from plugins.Bots.DiscordBot.bot import DiscordBot
from plugins.Google.google import Google
from plugins.Web.server import WebServer
from jobs.updater import start
from utils import dataBases

mongoDataBase = dataBases.mongodb_client


async def main():
    """
    Main function
    Set up and start application
    """

    # ------------------------------------------------------------------------------------------------------------------

    DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

    # MONGODATABASE_HOST = os.getenv('MONGODATABASE_HOST', '')
    # MONGODATABASE_USER = os.getenv('MONGODATABASE_USER', '')
    # MONGODATABASE_PASSWORD = os.getenv('MONGODATABASE_PASSWORD', '')

    WEBAPP_HOST = '0.0.0.0'
    WEBAPP_PORT = int(os.getenv('PORT', '8000'))

    # ------------------------------------------------------------------------------------------------------------------

    # mongoDataBase = MongoDataBase(host=MONGODATABASE_HOST, user=MONGODATABASE_USER, passwd=MONGODATABASE_PASSWORD)

    google = Google(os.getenv('GOOGLE_API_KEY'), os.getenv('GOOGLE_ENGINE_ID'))

    discordBot = DiscordBot(mongoDataBase=mongoDataBase, google=google)

    webServer = WebServer(mongoDataBase=mongoDataBase, discordBot=discordBot, google=google)

    runner = AppRunner(webServer.client)
    await runner.setup()

    site = TCPSite(runner=runner, host=WEBAPP_HOST, port=WEBAPP_PORT, shutdown_timeout=60)
    await site.start()

    # Start scheduler
    if not os.getenv('DEBUG', '0').lower() in ['true', 't', '1']:
        start()

    # if not discord.opus.is_loaded():
    #     discord.opus.load_opus('./libopus.so.0.8.0')

    await discordBot.client.start(token=DISCORD_BOT_TOKEN)

    await runner.cleanup()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
