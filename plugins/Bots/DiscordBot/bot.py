"""
DiscordBot plugin to work with discord
"""
import gettext
import discord

from typing import Union, Optional, Any
from plugins.Bots.DiscordBot.handlers import DiscordBotHandler
from plugins.Bots.DiscordBot.commands import DiscordBotCommand

command_permission = {
    'voice': {
        'init': 'admin',
    }
}

command_description = {
    'bot': {
        'join': 'Join bot to your voice channel',
        'ping': 'Show latency of the bot',
        'leave': 'Leave bot from the voice channel',
    },
    'fun': {
        'quote': 'Get random quote with author',
        'horoscope': 'Get horoscope for current day',
    },
    'voice': {
        'init': 'Set/Unset voice channel as init channel',
        'mute': 'Mute or unmute someone in voice channel',
        'deaf': 'Deaf or undead someone in voice channel',
        'move': 'Move someone in your voice channel',
        'disconnect': 'Disconnect someone from voice channel',
        'owner': 'Show/Give owner of the category',
        'rename': 'Rename voice channel',
        'member': 'Allow/Deny access for member to voice channel',
        'role': 'Allow/Deny access for role to voice channel',
        'lock': 'Lock/Unlock voice channel',
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
        'queue': 'Show queue of the server',
        'pause': 'Pause or resume playing music',
        'skip': 'Skip current playing track',
        'now': 'Show currently playing track',
        'seek': 'Go to position in currently playing track',
        'clear': 'Clear music queue. Count of elements to delete (n > 0 from start, n < 0 from end, n = 0 clear all)',
    },
    'member': {
        'avatar': 'Get avatar of user',
    },
}


class DiscordBot:
    """
    Class to work with discord
    """

    def __init__(self, intents=discord.Intents.all(), mongoDataBase=None, **options: Any):
        self.client = discord.Client(intents=intents)
        self.mongoDataBase = mongoDataBase
        self.discordBotCommand = DiscordBotCommand(mongoDataBase=mongoDataBase)

    async def set_default_commands(self, guild=None):
        try:
            commandTree = discord.app_commands.CommandTree(self.client)
            groups = {}

            for handler in [handler for handler in dir(DiscordBotCommand) if not handler.startswith('__')]:
                group_name, name = handler.split(sep='_', maxsplit=1)
                # name = handler
                description = command_description.get(group_name, {}).get(name, name)
                callback = getattr(self.discordBotCommand, handler)

                command = discord.app_commands.Command(name=name, description=description, callback=callback)

                if 'admin' == command_permission.get(group_name, {}).get(name, ''):
                    command.default_permissions = None

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
