from datetime import datetime, timedelta

from pytz import utc

from utils import cache
from utils import dataBases

mongoDataBase = dataBases.mongodb_client


def stats_sync(query=None, filter=None):
    from jobs.updater import sched

    if query and filter:
        mongoUpdate = mongoDataBase.update_field(database_name='dbot', collection_name='guilds',
                                                 action='$inc', filter=filter, query=query)

        if mongoUpdate is None:
            date = datetime.now(tz=utc) + timedelta(minutes=15)
            date = date.strftime('%Y-%m-%d %H:%M:%S')
            return sched.get_job('stats_sync').modify(date=date, args=[query, filter])
        else:
            return sched.get_job('stats_sync').modify(args=[])

    if not mongoDataBase.check_connection():
        return

    for guild_id in cache.stats.keys():
        query = {'xp': 1}
        filter = {'id': guild_id}
        document = mongoDataBase.get_document(database_name='dbot',
                                              collection_name='guilds',
                                              filter=filter,
                                              query=query)

        guild_xp = document.get('xp', {})

        cache.stats[guild_id]['xp']['message_xp'] = guild_xp.get('message_xp', 100)
        cache.stats[guild_id]['xp']['voice_xp'] = guild_xp.get('voice_xp', 50)
        cache.stats[guild_id]['xp']['message_xp_delay'] = guild_xp.get('message_xp_delay', 60)

        query = {}

        for member_id in cache.stats.get(guild_id, {}).get('members', {}).keys():
            try:
                voicetime = cache.stats.get(guild_id, {}).get('members', {}).get(member_id, {}).pop('voicetime')
            except Exception as e:
                voicetime = 0

            if not voicetime == 0:
                query[f'members.{member_id}.stats.voicetime'] = voicetime

            try:
                messages_count = cache.stats.get(guild_id, {}).get('members', {}).get(member_id, {}).pop(
                    'messages_count')
            except Exception as e:
                messages_count = 0

            if not messages_count == 0:
                query[f'members.{member_id}.stats.messages_count'] = messages_count

            try:
                reactions_count = cache.stats.get(guild_id, {}).get('members', {}).get(member_id, {}).pop(
                    'reactions_count')
            except Exception as e:
                reactions_count = 0

            if not reactions_count == 0:
                query[f'members.{member_id}.stats.reactions_count'] = reactions_count

            try:
                messages_count_xp = cache.stats.get(guild_id, {}).get('members', {}).get(member_id, {}).pop(
                    'messages_count_xp')
            except Exception as e:
                messages_count_xp = 0

            if not messages_count_xp == 0 or not voicetime == 0:
                message_xp = cache.stats.get(guild_id, {}).get('xp', {}).get('message_xp', 100)
                voice_xp = cache.stats.get(guild_id, {}).get('xp', {}).get('voice_xp', 50)

                xp = (messages_count_xp * message_xp) + ((voicetime // 60) * voice_xp)

                query[f'members.{member_id}.stats.xp'] = xp

            # del cache.stats[guild_id]['members'][member_id]['messages_count']

        mongoUpdate = mongoDataBase.update_field(database_name='dbot', collection_name='guilds',
                                                      action='$inc', filter=filter, query=query)

        if mongoUpdate is None:
            date = datetime.now(tz=utc) + timedelta(minutes=15)
            date = date.strftime('%Y-%m-%d %H:%M:%S')
            sched.get_job('stats_sync').modify(next_run_time=date, args=[query, filter])
