import logging
import gevent

from django.db import transaction
from django.core.management.base import BaseCommand

from core.models import Base

logger = logging.getLogger("core.executors.remote")


class Command(BaseCommand):
    args = '<poll_id poll_id ...>'
    help = 'Recreate all stopped or running workers'

    def handle(self, *args, **options):
        def _handle_base(base):
            base.stop()
            base.destroy()
            base.start()

        greenlets = []

        transaction.set_autocommit(False)
        for base in Base.objects.filter(executor__pid__isnull=False).select_for_update(nowait=False):
            g = gevent.spawn(_handle_base, base)
            greenlets.append(g)
        gevent.wait(greenlets)
        transaction.commit()
        transaction.set_autocommit(True)
