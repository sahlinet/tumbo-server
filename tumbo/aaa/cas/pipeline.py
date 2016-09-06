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
    # workaround for creating internalid
    user.authprofile.internalid = user.authprofile.internalid
    user.authprofile.save()
    logger.info("create_ticket pipeline for user %s" % user.username)
    if "next" in backend.strategy.session:
        next = backend.strategy.session['next']

        ticket = Ticket.objects.create_ticket(user=user)
        logger.info("Create ticket for user %s" % user.username)

        backend.strategy.session['next'] = "%s?ticket=%s" % (next, ticket.ticket)
        logger.info("Setting next URL: %s" % backend.strategy.session['next'])
    else:
        logger.info("Next missing")
