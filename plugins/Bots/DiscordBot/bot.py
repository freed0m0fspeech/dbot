"""
DiscordBot plugin to work with discord
"""
import discord

from typing import Any
from collections import defaultdict
from plugins.Bots.DiscordBot.commands import DiscordBotCommand

command_description = {
    'bot': {
        'join': 'Join bot to your voice channel',
        'ping': 'Show latency of the bot',
        'leave': 'Leave bot from voice channel',
    },
    'fun': {
        'quote': 'Get random quote',
        'horoscope': 'Get horoscope for current day',
    },
    'voice': {
        'init': 'Set/Unset/Create voice channel as init voice channel',
        'mute': 'Mute or unmute someone in the voice channel',
        'deaf': 'Deaf or undead someone in the voice channel',
        'move': 'Move someone in your voice channel',
        'disconnect': 'Disconnect someone from the voice channel',
        'owner': 'Show/Give owner of the voice channel',
        'name': 'Change name of the voice channel',
        'member': 'Allow/Deny access for member to the voice channel',
        'role': 'Allow/Deny access for role to the voice channel',
        'lock': 'Lock/Unlock the voice channel',
        'limit': 'Change user limit of the voice channel'
    },
    'server': {
        'prefix': 'Change prefix of the server',
        'members': 'Count of members on server',
        'moderator': 'Add/delete moderator for bot',
        'administrator': 'Add/delete administrator for bot',
        'no_command_channel': 'Add/delete channel to/from ignore command list',
        'system_channel': 'Set/Unset system channel for the guild',
    },
    'music': {
        'play': 'Play music from YouTube',
        'queue': 'Show music queue of the server',
        'pause': 'Pause or resume playing music',
        'skip': 'Skip currently playing music',
        'now': 'Show currently playing music',
        'seek': 'Go to position in currently playing music',
        'clear': 'Clear music queue',
        'lyrics': 'Lyrics for title or currently playing music'
    },
    'member': {
        'avatar': 'Get avatar of user',
    },
}


class DiscordBot:
    """
    Class to work with discord
    """

    def __init__(self, intents=discord.Intents.all(), mongoDataBase=None, google=None, **options: Any):
        self.client = discord.Client(intents=intents)
        self.mongoDataBase = mongoDataBase
        self.discordBotCommand = DiscordBotCommand(self, mongoDataBase=mongoDataBase)
        self.google = google

        # Cached guilds
        self.guilds = {}

        query = {'_id': 0, 'id': 1, 'temporary': 1, 'members': 1}
        for guild in self.mongoDataBase.get_documents(database_name='dbot', collection_name='guilds', query=query):
            self.guilds[guild.get('id', '')] = guild

        self.music = defaultdict(lambda: defaultdict(list))

    async def set_default_commands(self, guild=None):
        try:
            commandTree = discord.app_commands.CommandTree(self.client)
            groups = {}

            for handler in [handler for handler in dir(DiscordBotCommand) if not handler.startswith('_')]:
                try:
                    group_name, name = handler.split(sep='_', maxsplit=1)
                except Exception as e:
                    continue

                description = command_description.get(group_name, {}).get(name, name)
                callback = getattr(self.discordBotCommand, handler)

                command = discord.app_commands.Command(name=name, description=description, callback=callback)

                if group_name:
                    group = groups.get(group_name, {})

                    if not group:
                        group = discord.app_commands.Group(name=group_name, description=group_name)
                        groups[group_name] = group

                    group.add_command(command, override=True)
                else:
                    commandTree.add_command(command, override=True, guild=guild)

            for group in groups.values():
                commandTree.add_command(group, override=True, guild=guild)

            await commandTree.sync(guild=guild)
        except Exception as e:
            print(e)

    async def clear_default_commands(self, guild=None):
        try:
            commandTree = discord.app_commands.CommandTree(self.client)
            commandTree.clear_commands(guild=guild)

            await commandTree.sync(guild=guild)
        except Exception as e:
            print(e)
