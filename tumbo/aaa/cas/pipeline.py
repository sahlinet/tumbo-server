from django.http import HttpResponse
from django.conf import settings

import logging

logger = logging.getLogger(__name__)

from aaa.cas.models import Ticket

def restrict_user(backend, user, response, *args, **kwargs):
    if hasattr(settings, "RESTRICTED_TO_USERS"):
        if _is_member(user):
            return HttpResponse("Not allowed to login")

def create_ticket(backend, user, response, *args, **kwargs):
    logger.info("create_ticket pipeline")
    if "next" in backend.strategy.session:
        next = backend.strategy.session['next']

        ticket = Ticket.objects.create_ticket(user=user)

        backend.strategy.session['next'] = "%s?ticket=%s" % (next, ticket.ticket)
        logger.info("Setting next URL: %s" % backend.strategy.session['next'])
    #kwargs['request'].user.session['next']=kwargs['request'].user.session['next']+"?ticket=asdf"
