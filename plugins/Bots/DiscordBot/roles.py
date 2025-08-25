import logging
import pandas as pd

from discord import Member, Guild, utils, Color
from random import random

bad_words = pd.read_csv('bad_words.csv', encoding='windows-1251')

stalker_words = ['зона', 'свет', 'знания']

game_roles = {
    'banana': '🐒 Мавпа',
    'dead by daylight': '🔪 Убийца',
    'world of tanks': '🥊 Пробитый',
    'among us': '🛸 Член экипажа',
    'rocket league': '♿ Инвалид',
    'rust': '⛏️ Клановый игрок',
    'terraria': '🌛 Лунный повелитель',
    'dota 2': '👨‍👩‍👦 Приемный',
    'league of legends': '🧙🏻‍♂️ Легенда',
    'minecraft': '🧊 Шахтер с алмазами',
    'deep rock galactic': '🪨 Камень',
    'valorant': '🪅 Калорантер',
    'r.e.p.o': '🤖 Репозиторщик',
    '7 days to die': '☠️ Зомби',
    "playerunknown's battlegrounds": '🎯 Патронофил',
    'roblox': '🧩 Блокостроитель',
    "don't starve together": '🍂 Выживальщик',
    'fortnite': '🪂 Строитель-боец',
    'the sims': '🏡 Домосед',
    'hearthstone': '🃏 Маг-карточник',
    'apex legends': '🪁 Прыгучий чемпион',
    'fall guys': '🤹‍♀️ Королевский шут',
    'destiny': '🌟 Страж Света',
    'genshin impact': '🍃 Путешественник стихий',
    'stardew valley': '🌾 Фермер мечты',
    'ark survival evolved': '🦖 Динодрессировщик',
}

partial_name_game_roles = {
    'diablo': '👹 Нефолем',
    'fifa': '⚽ Офсайдер',
    'call of duty': '🪖 Генерал диванных войск',
    'civilization': '🏹 Парашник',
    'overwatch': '💦 Овердрочер',
    'counter-strike': '🕌 Сын миража',
    'grand theft auto': '💲 Бомж-миллионер',
    'escape from tarkov': '🦟 Тарковский комар',
    "tom clancy's rainbow six siege": '🌈 Оператор дронов',
    'starcraft': '⭐ Адепт',
    'poker': '🃏 Шулер',
    'need for speed': '🏎️ Гонщик',
    'dark souls': '💨 Повелитель пепла',
    "baldur's gate": '🗡️ Ролевой маньяк',
    "assassin's creed": '🩸 Теневой убийца',
    'the witcher': '🧛‍♂️ Ведьмак тьмы',
    'skyrim': '🐺 Драконоборец',
    'borderlands': '🔫 Лутер-пират',
    'portal': '🌀 Тестовый субъект',
    'quake': '💣 Боец арены',
    'doom': '🔥 Демоноборец',
    'age of empires': '🏰 Император времён',
    'warcraft': '🪓 Оркоборец',
    'left 4 dead': '🧟‍♂️ Командный выживальщик',
    'bioshock': '🔱 Подводный авантюрист',
    'cyberpunk 2077': '🌃 Ночной гонщик',
    'sea of thieves': '🏴‍☠️ Пират карибский',
    'watch dogs': '💻 Хакер улиц',
    'subnautica': '🌊 Морской исследователь',
}

reaction_roles = {
    '🥺': '🥺 Милашка',
    '😢': '😢 Плакса',
    '🌶️': '🌶️ Перченый',
    '🚩': '🚩 Ред флаг',
    '💩': '💩 Какашка',
    '🔥': '🔥 Обжигатель',
    '🤡': '🤡 Клоун',
    '👎': '🤬 Хейтер',
    '👍': '🥰 Доброжелатель',
}

reaction_name_roles = {
    'worldwarz': '🪆 Пешка Кремля',
    'amongus': '💀 Импостер',
    'worldoftanks': '🦀 Ракообразный',
}

# drop rows with different language
# bad_words = bad_words[bad_words['language'] == 'ru']

async def roll_role(member: Member, guild: Guild, name: str, rate=3):
    """
    Roll the role for guild member at given chance rate and name
    If no role is created in guild, creates it automatically

    :param member:
    :param guild:
    :param name:
    :param rate:
    """
    if guild and member and name:
        if not rate == 0:
            if not random() < (10 ** -rate):
                return

        if not utils.get(member.roles, name=name):
            role = utils.get(guild.roles, name=name)

            if not role:
                role = await guild.create_role(name=name, color=Color.random(), hoist=True)

            await member.add_roles(role)
            await member.send(f'Поздравляю. Ты разблокировал(а) секретную роль: {role.name}')

            await secret_roles(member, guild, 'getting new role')

async def secret_roles(member: Member, guild: Guild, event: str, *attrs):
    if member and guild and event:
        if member.bot:
            return

        logging.info(f'Secret role event: "{event}" received, member: @{member.name}')

        if event == 'activity updated':
            if attrs:
                activity = attrs[0]

                if not hasattr(activity, 'name'):
                    return

                if not hasattr(activity, 'application_id'):
                    return

                activity_name = activity.name.lower()

                role_name = game_roles.get(activity_name, '')
                if role_name:
                    await roll_role(member=member, guild=guild, name=f'{role_name}', rate=3)
                else:
                    role_names = list(filter(None, [partial_name_game_roles.get(word, '') for word in activity_name.split()]))
                    if role_names:
                        role_name = role_names.pop()
                        await roll_role(member=member, guild=guild, name=f'{role_name}', rate=3)

            return await roll_role(member=member, guild=guild, name='🎯 Геймер', rate=3)

        if event == 'joining voice channel':
            return await roll_role(member=member, guild=guild, name='👣 Бродяга', rate=3)

        if event == 'leaving last from temporary voice channel':
            return await roll_role(member=member, guild=guild, name='🧨 Уничтожитель', rate=3)

        if event == 'creation of new temporary voice channel':
            return await roll_role(member=member, guild=guild, name='💥 Создатель', rate=3)

        if event == 'being in voice channel 6.9 or more hours':
            return await roll_role(member=member, guild=guild, name='♋ Живая легенда', rate=3)

        if event == 'sending message':
            if attrs:
                content = attrs[0]

                # sending toxic message
                if any([word in content for word in bad_words['word']]):
                    await roll_role(member=member, guild=guild, name='🤢 Токсик', rate=3)

                # Chance to get role for sending message with . in the end of sentence (1 in 1.000)
                if content.endswith('.'):
                    await roll_role(member=member, guild=guild, name='🤓 Душнила', rate=3)

                # Chance to get role for sending message 'пам' in sentence (1 in 1.000)
                if 'пам' in content:
                    await roll_role(member=member, guild=guild, name='💢 Пам', rate=3)

                if any([word in content for word in stalker_words]):
                    await roll_role(member=member, guild=guild, name='👀 Сталкер', rate=3)

            return await roll_role(member=member, guild=guild, name='🍀 Лакер', rate=5)

        if event == 'self mute action':
            return await roll_role(member=member, guild=guild, name='🤐 Молчун', rate=3)

        if event == 'self deaf action':
            return await roll_role(member=member, guild=guild, name='🙉 Глухонемой', rate=3)

        if event == 'self stream action':
            return await roll_role(member=member, guild=guild, name='🎬 Режиссер', rate=3)

        if event == 'self video action':
            return await roll_role(member=member, guild=guild, name='🔞 Порнозвезда', rate=3)

        if event == 'using command /music play':
            return await roll_role(member=member, guild=guild, name='🎵 Диджей', rate=3)

        if event == 'adding reaction to message':
            if attrs:
                reaction = attrs[0]

                if hasattr(reaction, 'name'):
                    reaction_name = reaction.name.lower()

                    role_name = reaction_name_roles.get(reaction_name, '')
                    if role_name:
                        await roll_role(member=member, guild=guild, name=f'{role_name}', rate=3)
                else:
                    role_name = reaction_roles.get(reaction, '')
                    if role_name:
                        await roll_role(member=member, guild=guild, name=f'{role_name}', rate=3)

            return await roll_role(member=member, guild=guild, name='☢️ Реактор', rate=3)

        if event == 'removing reaction from message':
            return await roll_role(member=member, guild=guild, name='☣️ Дезинтегратор', rate=3)

        if event == 'creation of thread':
            return await roll_role(member=member, guild=guild, name='🧵 Поточек', rate=3)

        if event == 'deleting message':
            return await roll_role(member=member, guild=guild, name='🗑️ Мусорщик', rate=3)

        if event == 'editing message':
            return await roll_role(member=member, guild=guild, name='✏️ Редактор', rate=3)

        if event == 'creating invite':
            return await roll_role(member=member, guild=guild, name='💌 Зазывала', rate=3)

        if event == 'getting new role':
            return await roll_role(member=member, guild=guild, name='💎 Коллекционер', rate=2)
