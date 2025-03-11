import logging
import pandas as pd

from discord import Member, Guild, utils, Color
from random import random

bad_words = pd.read_csv('bad_words.csv', encoding='windows-1251')
stalker_words = ['зона', 'свет', 'знания']

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

                if activity_name == 'banana':
                    return await roll_role(member=member, guild=guild, name='🐒 Мавпа', rate=3)
                elif activity_name == 'dead by daylight':
                    return await roll_role(member=member, guild=guild, name='🔪 Убийца', rate=3)
                elif activity_name == 'world of tanks':
                    return await roll_role(member=member, guild=guild, name='🥊 Пробитый', rate=3)
                elif activity_name == 'among us':
                    return await roll_role(member=member, guild=guild, name='🛸 Член экипажа', rate=3)
                elif activity_name == 'rocket league':
                    return await roll_role(member=member, guild=guild, name='♿ Инвалид', rate=3)
                elif activity_name == 'rust':
                    return await roll_role(member=member, guild=guild, name='⛏️ Клановый игрок', rate=3)

                elif 'counter-strike'in activity_name:
                    return await roll_role(member=member, guild=guild, name='🕌 Сын миража', rate=3)
                elif 'grand theft auto' in activity_name:
                    return await roll_role(member=member, guild=guild, name='👩🏻‍💼 Офисный планктон', rate=3)
                elif 'escape from tarkov' in activity_name:
                    return await roll_role(member=member, guild=guild, name='🦟 Тарковский комар', rate=3)
                elif "tom clancy's rainbow six siege" in activity_name:
                    return await roll_role(member=member, guild=guild, name='🌈 Радужный', rate=3)

            return

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
                    if reaction_name == 'worldwarz':
                        await roll_role(member=member, guild=guild, name='🪆 Пешка Кремля', rate=3)
                    elif reaction_name == 'amongus':
                        await roll_role(member=member, guild=guild, name='💀 Импостер', rate=3)
                    elif reaction_name == 'worldoftanks':
                        await roll_role(member=member, guild=guild, name='🦀 Ракообразный', rate=3)
                else:
                    if reaction == '👍':
                        await roll_role(member=member, guild=guild, name='🥰 Доброжелатель', rate=3)
                    elif reaction == '👎':
                        await roll_role(member=member, guild=guild, name='🤬 Хейтер', rate=3)
                    elif reaction == '🤡':
                        await roll_role(member=member, guild=guild, name='🤡 Клоун', rate=3)
                    elif reaction == '🔥':
                        await roll_role(member=member, guild=guild, name='🔥 Обжигатель', rate=3)
                    elif reaction == '💩':
                        await roll_role(member=member, guild=guild, name='💩 Какашка', rate=3)
                    elif reaction == '🚩':
                        await roll_role(member=member, guild=guild, name='🚩 Ред флаг', rate=3)
                    elif reaction == '🌶️':
                        await roll_role(member=member, guild=guild, name='🌶️ Перченый', rate=3)

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
