import json

import discord

default_role = discord.PermissionOverwrite(
    view_channel=True,
    manage_channels=False,
    manage_permissions=False,
    manage_webhooks=False,
    create_instant_invite=True,
    send_messages=True,
    embed_links=True,
    attach_files=True,
    add_reactions=True,
    use_external_emojis=False,
    mention_everyone=False,
    manage_messages=False,
    read_message_history=True,
    send_tts_messages=False,
    # use_slash_commands=True,
    connect=True,
    speak=True,
    stream=True,
    use_voice_activation=True,
    priority_speaker=False,
    mute_members=False,
    deafen_members=False,
    move_members=False
)

owner_role = discord.PermissionOverwrite(
    view_channel=True,
    manage_channels=True,
    manage_permissions=True,
    manage_webhooks=True,
    create_instant_invite=True,
    send_messages=True,
    embed_links=True,
    attach_files=True,
    add_reactions=True,
    use_external_emojis=True,
    mention_everyone=True,
    manage_messages=True,
    read_message_history=True,
    send_tts_messages=True,
    # use_slash_commands=True,
    connect=True,
    speak=True,
    stream=True,
    use_voice_activation=True,
    priority_speaker=True,
    mute_members=True,
    deafen_members=True,
    move_members=True
)
