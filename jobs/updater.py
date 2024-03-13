import logging

from datetime import datetime, timedelta
from apscheduler.events import (
    EVENT_JOB_EXECUTED,
    EVENT_JOB_ERROR
)
from apscheduler.schedulers.background import BackgroundScheduler
from jobs.jobs import (
    stats_sync
)
from pytz import utc


# executors = {
#     'default': ThreadPoolExecutor(1)
# }

def listener(event):
    # print(event.__dict__)
    # {
    #     'code': 4096,
    #     'alias': None,
    #     'job_id': 'test',
    #     'jobstore': 'default',
    #     'scheduled_run_time': datetime.datetime(2023, 8, 16, 0, 49, 56, 335206, tzinfo= < UTC >),
    #     'retval': None,
    #     'exception': None,
    #     'traceback': None
    # }
    if event.exception:
        # print(f'The job {event.job_id}() crashed :(')
        logging.info(f'The job {event.job_id}() crashed :(')
    else:
        # print(f'The job {event.job_id}() executed successfully :)')
        logging.info(f'The job {event.job_id}() executed successfully :)')


job_defaults = {
    'coalesce': True,
    'max_instances': 1,
    'misfire_grace_time': None,
}

sched = BackgroundScheduler(timezone=utc, job_defaults=job_defaults)
sched.add_listener(listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)


def start():
    sched.add_job(stats_sync, 'interval', hours=1, id='stats_sync',
                  misfire_grace_time=None, coalesce=True)

    sched.start()

    sched.print_jobs()
