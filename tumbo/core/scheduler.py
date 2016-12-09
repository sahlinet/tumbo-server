import logging
import time
from django.conf import settings
from django import db

from pytz import utc

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from django.core.management import call_command

from core.models import Apy
from core.utils import call_apy

logger = logging.getLogger(__name__)


def cron_to_dict(cronexpr):
    """
    See https://apscheduler.readthedocs.org/en/latest/modules/triggers/cron.html?highlight=cron#module-apscheduler.triggers.cron
    """
    expr_list = cronexpr.split(" ")
    cron_dict = {}
    cron_dict['second'] = expr_list[0]
    cron_dict['minute'] = expr_list[1]
    cron_dict['hour'] = expr_list[2]
    cron_dict['day_of_week'] = expr_list[3]
    return cron_dict


def update_job(apy, scheduler):
    job_id = "%s-%s-%s" % (apy.base.user.username, apy.base.name, apy.name)
    if apy.schedule:
        time.sleep(0.1)
        kwargs = cron_to_dict(apy.schedule)
        if scheduler.get_job(job_id):
            scheduler.reschedule_job(job_id, trigger='cron', **kwargs)
            logger.debug("Job '%s' rescheduled" % job_id)
        else:
            job_id = scheduler.add_job(call_apy, 'cron', args=[apy.base.name, apy.name], id=job_id, **kwargs)
            logger.info("Job '%s' added" % job_id)
    else:
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            logger.info("Job '%s' removed" % job_id)


def start_scheduler():

    jobstores = {
        'default': SQLAlchemyJobStore(url=settings.TUMBO_SCHEDULE_JOBSTORE)
    }

    executors1 = {
        'default': ThreadPoolExecutor(5)
    }

    job_defaults = {
        'coalesce': False,
        'max_instances': 1
    }

    scheduler = BackgroundScheduler(executors=executors1, jobstores=jobstores, job_defaults=job_defaults, timezone=utc)

    # Cleanup
    if hasattr(settings, "TUMBO_CLEANUP_INTERVAL_MINUTES"):
        job_id = scheduler.add_job(call_command, 'interval', minutes=int(settings.TUMBO_CLEANUP_INTERVAL_MINUTES), args=["cleanup_transactions"])
        logger.info(job_id)

    time.sleep(1)
    scheduler.start()

    while True:
        logger.debug("START rescheduling call_apy")
        for apy in Apy.objects.all():
            try:
                update_job(apy, scheduler)
            except Exception:
                if not apy.schedule:
                    logger.exception("Problem with schedule config for %s: %s" % (apy.name, apy.schedule))
        logger.debug("END rescheduling call_apy")
        db.reset_queries()
        time.sleep(120)

