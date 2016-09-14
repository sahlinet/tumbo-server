import logging
import datetime
import pytz

from django.conf import settings
from django.core.management.base import BaseCommand

from core.models import Transaction, LogEntry

logger = logging.getLogger("core.executors.remote")


class Command(BaseCommand):
    help = 'Cleanup old transactions and logs'

    def handle(self, *args, **options):
        older_than = datetime.datetime.now()-datetime.timedelta(hours=settings.TUMBO_CLEANUP_OLDER_THAN_N_HOURS)
        older_than_aware = older_than.replace(tzinfo=pytz.UTC)
        transactions = Transaction.objects.filter(created__lte=older_than_aware)

        import time
        while transactions.count():
            time.sleep(0.1)
            ids = transactions.values_list('pk', flat=True)[:100]
            Transaction.objects.filter(pk__in = ids).delete()

        logger.info("Deleting %s transactions" % transactions.count())
        logs = LogEntry.objects.filter(created__lte=older_than_aware)
        logger.info("Deleting %s logentries" % logs.count())
