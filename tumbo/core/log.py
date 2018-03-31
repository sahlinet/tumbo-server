import logging
import json
from core.communication import CommunicationThread
from core.models import Transaction
import newrelic.agent

logger = logging.getLogger(__name__)


class LogReceiverThread(CommunicationThread):

    @newrelic.agent.background_task(name='log-receiver', group='QueueConsumer')
    def on_message(self, ch, method, props, body):
        logger.debug("Message received")
        try:
            data = json.loads(body)
            level = data['level']
            if level == logging.DEBUG:
                logger.debug(data)
            elif level == logging.INFO:
                logger.info(data)
            elif level == logging.WARNING:
                logger.warning(data)
            elif level == logging.ERROR:
                logger.error(data)
            elif level == logging.CRITICAL:
                logger.critical(data)
            transaction = Transaction.objects.get(rid=data['rid'])
            transaction.log(data['level'], data['msg'])
        except Exception, e:
            logger.exception(e)
