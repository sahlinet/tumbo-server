import logging

from aaa.cas.models import Ticket


logger = logging.getLogger(__name__)


def create_ticket(backend, user, response, *args, **kwargs):
    """
    If a user authenticates we need to create a ticket for the user and set next in session session
    to the service URL with the ticket as GET parameter
    """
    logger.info("create_ticket pipeline for user %s started" % user.username)

    # workaround for creating internalid
    user.authprofile.internalid = user.authprofile.internalid
    user.authprofile.save()

    if "next" in backend.strategy.session:
        next = backend.strategy.session['next']
        logger.info("create_ticket next is: %s" % next)

        ticket = Ticket.objects.create_ticket(user=user)
        logger.info("Create ticket for user %s" % user.username)

        # attach the ticket to the next URL
        backend.strategy.session['next'] = "%s?ticket=%s" % (next, ticket.ticket)
        logger.info("Setting next URL: %s" % backend.strategy.session['next'])
    else:
        logger.info("Next missing")

    logger.info("create_ticket pipeline for user %s ended" % user.username)
