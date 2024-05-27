import logging

from discord import Member, Guild, utils, Color
from random import random

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

async def secret_roles(member: Member, guild: Guild, event: str):
    if member and guild and event:
        if member.bot:
            return

        logging.info(f'Secret role event: "{event}" received, member: @{member.name}')

        if event == 'joining voice channel':
            return await roll_role(member=member, guild=guild, name='👣 Бродяга', rate=3)
        if event == 'leaving last from temporary voice channel':
            return await roll_role(member=member, guild=guild, name='🧨 Уничтожитель', rate=3)
        if event == 'creation of new temporary voice channel':
            return await roll_role(member=member, guild=guild, name='💥 Создатель', rate=3)
        if event == 'being in voice channel 6.9 or more hours':
            return await roll_role(member=member, guild=guild, name='♋ Живая легенда', rate=3)

        if event == 'sending message':
            return await roll_role(member=member, guild=guild, name='🍀 Лакер', rate=5)
        if event == 'sending toxic message':
            return await roll_role(member=member, guild=guild, name='🤢 Токсик', rate=3)
        if event == 'sending message with . in the end of sentence':
            return await roll_role(member=member, guild=guild, name='🤓 Душнила', rate=3)
        if event == 'sending message пам in sentence':
            return await roll_role(member=member, guild=guild, name='💢 Пам', rate=3)

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
