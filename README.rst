discord-bot-freed0m0fspeech
========================

Discord bot for Freedom of speech, Python project.

`Learn more about bot <https://github.com/pr0stre1/dbot/releases>`_.

---------------

Additional info about ``dbot`` file, you can find `here <https://github.com/pr0stre1/dbot/releases>`_.

---------------

Commands:

  Commands to interact with bot (/bot):

  * /join - Join bot to your voice channel
  * /ping - Show latency of the bot
  * /leave - Leave bot from the voice channel

  Commands for fun (/fun):

  * /quote - Get random quote with author
  * /horoscope [sign] - Get horoscope for current day

  Commands to interact with voice channels (/voice):

  * /mute @user- Mute or unmute someone in voice channel
  * /deaf @user - Deaf or undead someone in voice channel
  * /move @user - Move someone in your voice channel
  * /disc @user - Disconnect someone from voice channel

  Commands to administrate some actions on channel (/server):

  * /prefix [new_prefix] - Change prefix of the server
  * /members - Count of members on server
  * /init moderator @user - Add/delete moderator for bot
  * /init administrator @user - Add/delete administrator for bot
  * /init no_command_channel #text-channel - Add/delete channel to/from ignore command list
  * /init system_channel #text-channel - Set/Unset system channel for the guild

  Commands to interact with music (/music):

  * /play [text/url] - Play music from YouTube
  * /queue - Show queue of the server
  * /pause - Pause or resume playing music
  * /skip - Skip current playing track
  * /now - Show currently playing track
  * /seek [hh:mm:ss] - Go to position in currently playing track
  * /clear [count] - Clear music queue. Count of elements to delete (n > 0 from start, n < 0 from end, n = 4 clear all)

  Commands to interact with temporaries (/temporary):

  * /category owner @user - Get/set owner of the category
  * /category init #voice-channel - Set/unset voice channel as init for temporary categories
  * /category rename [new_name] - Rename temporary category
  * /category invite_member @user - Invite/delete member to/from temporary category
  * /category invite_role @role - Invite/delete role to/from temporary category
  * /category lock - Lock/unlock category
  * /category disc_member @user - Disconnect member from temporary category voice channel

  Commands to interact with members (/member):

  * /avatar @user - Get avatar of user

---------------

Functionality:

  * Temporary categories (with voice channels)
  * Saving music queue and important information to database
  * Interactive responses
