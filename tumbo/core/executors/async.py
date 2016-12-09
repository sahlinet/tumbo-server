import logging
import time
import json
import sys

from core.models import Transaction, FINISHED
from core.queue import CommunicationThread

logger = logging.getLogger(__name__)


class AsyncResponseThread(CommunicationThread):

    def on_message(self, ch, method, props, body):
        try:
            logger.debug(self.name+": "+sys._getframe().f_code.co_name)
            data = json.loads(body)

            try:
                returned = json.loads(data['returned'])
                data['returned'] = returned
            except Exception, e:
                logger.exception("Could not load data['returned']")

            logger.info("Async response received for rid '%s'" % data['rid'])
            logger.info(data)

            transaction = Transaction.objects.get(pk=data['rid'])
            transaction.tout = data
            transaction.status = FINISHED
            transaction.save()

        except Exception, e:
            logger.exception(e)
        time.sleep(0.01)
