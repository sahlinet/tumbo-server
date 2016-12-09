from __future__ import unicode_literals

import logging
import time

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _



logger = logging.getLogger(__name__)

class InvalidTicket(Exception):
    pass


class TicketManager(models.Manager):
    def create_ticket(self, ticket=None, **kwargs):
        if not ticket:
            ticket = self.create_ticket_str()
        if 'service' in kwargs:
            kwargs['service'] = clean_service_url(kwargs['service'])
        if 'expires' not in kwargs:
            expires = now() + timedelta(seconds=30)
            kwargs['expires'] = expires
        t = self.create(ticket=ticket, **kwargs)
        logger.debug("Created %s %s" % (t.user.username, t.ticket))
        return t

    def create_ticket_str(self, prefix=None):
        """
        Generate a sufficiently opaque ticket string to ensure the ticket is
        not guessable. If a prefix is provided, prepend it to the string.
        """
        #if not prefix:
        #    prefix = self.model.TICKET_PREFIX
        return "%s-%d-%s" % (prefix, int(time.time()),
                             get_random_string(length=20))

    def validate_ticket(self, ticket, service, renew=False, require_https=False):
        """
        Given a ticket string and service identifier, validate the
        corresponding ``Ticket``. If validation succeeds, return the
        ``Ticket``. If validation fails, raise an appropriate error.
        If ``renew`` is ``True``, ``ServiceTicket`` validation will
        only succeed if the ticket was issued from the presentation
        of the user's primary credentials.
        If ``require_https`` is ``True``, ``ServiceTicket`` validation
        will only succeed if the service URL scheme is HTTPS.
        """
        if not ticket:
            raise InvalidRequest("No ticket string provided")

        #if not self.model.TICKET_RE.match(ticket):
        #    raise InvalidTicket("Ticket string %s is invalid" % ticket)

        try:
            t = self.get(ticket=ticket)
        except self.model.DoesNotExist:
            raise InvalidTicket("Ticket %s does not exist" % ticket)

        #if t.is_consumed():
        #    raise InvalidTicket("%s %s has already been used" %
        #                        (t.name, ticket))
        if t.is_expired():
            raise InvalidTicket("%s %s has expired" % (t.user.username, ticket))

        logger.debug("Validated %s %s" % (t.user.username, ticket))
        return t


class Ticket(models.Model):
    ticket = models.CharField(_('ticket'), primary_key=True, max_length=255, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('user'))
    expires = models.DateTimeField(_('expires'))
    consumed = models.DateTimeField(_('consumed'), null=True)

    objects = TicketManager()

    def __str__(self):
        return self.ticket

    def consume(self):
        self.consumed = now()
        self.save()

    def is_expired(self):
        return self.expires <= now()

