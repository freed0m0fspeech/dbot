"""
DiscordBot plugin to work with discord
"""
import discord

from typing import Any
from collections import defaultdict
from plugins.Bots.DiscordBot.commands import DiscordBotCommand

command_description = {
    'bot': {
        'join': {
            "en-US": 'Join bot to your voice channel',
            "ru-RU": 'Подключение бота к своему голосовому каналу',
            "default": "en-US",
        },
        'ping': {
            "en-US": 'Show latency of the bot',
            "ru-RU": 'Показать задержку бота',
            "default": "en-US",
        },
        'leave': {
            "en-US": 'Leave bot from voice channel',
            "ru-RU": 'Кикнуть бота из голосового канала',
            "default": "en-US",
        },
    },
    'fun': {
        'quote': {
            "en-US": 'Get random quote',
            "ru-RU": 'Рандомная цитата',
            "default": "en-US",
        },
        'horoscope': {
            "en-US": 'Get horoscope for current day',
            "ru-RU": 'Гороскоп на текущий день',
            "default": "en-US",
        },
    },
    'voice': {
        'init': {
            "en-US": 'Set/Unset/Create voice channel as init voice channel',
            "ru-RU": 'Установить/Снять/Создать голосовоой канал для создания голосовых каналов',
            "default": "en-US",
        },
        'mute': {
            "en-US": 'Mute/Unmute someone in the voice channel',
            "ru-RU": 'Замутать/Размутать кого-то в голосовом канале',
            "default": "en-US",
        },
        'deaf': {
            "en-US": 'Deaf/Udead someone in the voice channel',
            "ru-RU": 'Заглушить/Разглушить кого-то в голосовом канале',
            "default": "en-US",
        },
        'move': {
            "en-US": 'Move someone in your voice channel',
            "ru-RU": 'Переместить кого-то в ваш голосовой канал',
            "default": "en-US",
        },
        'disconnect': {
            "en-US": 'Disconnect someone from the voice channel',
            "ru-RU": 'Отключить кого-то из вашего голосового канала',
            "default": "en-US",
        },
        'owner': {
            "en-US": 'Show/Give owner of the voice channel',
            "ru-RU": 'Показать/Изменить владельца голосового канала',
            "default": "en-US",
        },
        'name': {
            "en-US": 'Change name of the voice channel',
            "ru-RU": 'Переименовать голосовой канал',
            "default": "en-US",
        },
        'member': {
            "en-US": 'Allow/Deny access for member to the voice channel',
            "ru-RU": 'Разрешить/Запретить доступ к голосовому каналу для участника',
            "default": "en-US",
        },
        'role': {
            "en-US": 'Allow/Deny access for role to the voice channel',
            "ru-RU": 'Разрешить/Запретить доступ к голосовому каналу для роли',
            "default": "en-US",
        },
        'lock': {
            "en-US": 'Lock/Unlock the voice channel',
            "ru-RU": 'Закрыть/Открыть голосовой канал',
            "default": "en-US",
        },
        'limit': {
            "en-US": 'Change user limit of the voice channel',
            "ru-RU": 'Изменить лимит пользователей для голосового канала',
            "default": "en-US",
        },
    },
    'server': {
        'prefix': {
            "en-US": 'Change prefix of the server',
            "ru-RU": 'Изменить префикс сервера',
            "default": "en-US",
        },
        'members': {
            "en-US": 'Count of members on server',
            "ru-RU": 'Количество участников на сервере',
            "default": "en-US",
        },
        'moderator': {
            "en-US": 'Add/delete moderator for bot',
            "ru-RU": 'Добавить/Удалить модератора бота',
            "default": "en-US",
        },
        'administrator': {
            "en-US": 'Add/delete administrator for bot',
            "ru-RU": 'Добавить/Удалить администратора бота',
            "default": "en-US",
        },
        'no_command_channel': {
            "en-US": 'Add/delete channel to/from ignore command list',
            "ru-RU": 'Добавить/Удалить канал из игнор-листа',
            "default": "en-US",
        },
        'system_channel': {
            "en-US": 'Set/Unset system channel for the guild',
            "ru-RU": 'Добавить/Удалить системный канал для сервера',
            "default": "en-US",
        },
    },
    'music': {
        'play': {
            "en-US": 'Play music from YouTube',
            "ru-RU": 'Воспроизвести музыку из Youtube',
            "default": "en-US",
        },
        'queue': {
            "en-US": 'Show music queue of the server',
            "ru-RU": 'Показать музыкальную очередь сервера',
            "default": "en-US",
        },
        'pause': {
            "en-US": 'Pause/Resume playing music',
            "ru-RU": 'Приостановить/Возобновить воспроизведение музыки',
            "default": "en-US",
        },
        'skip': {
            "en-US": 'Skip currently playing music',
            "ru-RU": 'Пропустить текущую музыку',
            "default": "en-US",
        },
        'now': {
            "en-US": 'Show currently playing music',
            "ru-RU": 'Показать текущю музыку',
            "default": "en-US",
        },
        'seek': {
            "en-US": 'Go to position in currently playing music',
            "ru-RU": 'Перемотать музыку',
            "default": "en-US",
        },
        'clear': {
            "en-US": 'Clear music queue',
            "ru-RU": 'Очистить музыкальную очередь',
            "default": "en-US",
        },
        'lyrics': {
            "en-US": 'Lyrics for title or currently playing music',
            "ru-RU": 'Текст песни по названию или для текущей музыки',
            "default": "en-US",
        },
    },
    'member': {
        'avatar': {
            "en-US": 'Get avatar of user',
            "ru-RU": 'Получить аватар пользователя',
            "default": "en-US",
        },
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

                locale = 'ru-RU'
                description = command_description.get(group_name, {}).get(name, {}).get(locale, name)
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
