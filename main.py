import asyncio
import os

from aiohttp.web import AppRunner, TCPSite
from dotenv import load_dotenv
from plugins.Bots.DiscordBot.bot import DiscordBot
from plugins.Web.server import WebServer
from plugins.DataBase.mongo import MongoDataBase
from jobs.updater import start

load_dotenv()


async def main():
    """
    Main function
    Set up and start application
    """

    # ------------------------------------------------------------------------------------------------------------------

    DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

    MONGODATABASE_HOST = os.getenv('MONGODATABASE_HOST', '')
    MONGODATABASE_USER = os.getenv('MONGODATABASE_USER', '')
    MONGODATABASE_PASSWORD = os.getenv('MONGODATABASE_PASSWORD', '')

    WEBAPP_HOST = '0.0.0.0'
    WEBAPP_PORT = int(os.getenv('PORT', '8000'))

    # ------------------------------------------------------------------------------------------------------------------

    mongoDataBase = MongoDataBase(host=MONGODATABASE_HOST, user=MONGODATABASE_USER, passwd=MONGODATABASE_PASSWORD)

    discordBot = DiscordBot(mongoDataBase=mongoDataBase)

    webServer = WebServer(mongoDataBase=mongoDataBase, discordBot=discordBot)

    runner = AppRunner(webServer.client)
    await runner.setup()

    site = TCPSite(runner=runner, host=WEBAPP_HOST, port=WEBAPP_PORT, shutdown_timeout=60)
    await site.start()

    # if not os.getenv('DEBUG', '0').lower() in ['true', 't', '1']:
    #     start()

    await discordBot.client.start(token=DISCORD_BOT_TOKEN)

    await runner.cleanup()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
