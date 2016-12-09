import logging
import requests

from urlparse import urlparse

from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.auth import login as auth_login

from core.models import Base
from core.utils import read_jwt

User = get_user_model()

logger = logging.getLogger(__name__)


def cas_login(function):
    def wrapper(request, *args, **kwargs):
        # logger.debug("authenticate %s" % request.user)
        user=request.user

        # if logged in
        if request.user.is_authenticated():
            logger.info("user.is_authenticated with user %s" % request.user.username)
            logger.info("user has internalid: %s" % request.user.authprofile.internalid)
            return function(request, *args, **kwargs)

        base = Base.objects.get(user__username=kwargs['username'], name=kwargs['base'])
        ticket = request.GET.get("ticket", None)
        if not ticket and (base.public or base.static_public):
            return function(request, *args, **kwargs)

        service = reverse('userland-static', args=[kwargs['username'], kwargs['base'], "index.html"])
        proto = request.META.get('HTTP_X_FORWARDED_PROTO', 'https')
        host = request.META.get('HTTP_X_FORWARDED_HOST', request.META.get('HTTP_HOST', None))
        if base.frontend_host:
            # if frontend_host is set, we do not want to present the backend uri in the service URL
            service_full = "%s://%s" % (proto, base.frontend_host)
        else:
            service_full = "%s://%s%s" % (proto, host, service)

        ticket = request.GET.get("ticket", None)

        if ticket:
            # if the service is called with a ticket, verify the ticket and redirect to the service
            cas_ticketverify=reverse('cas-ticketverify')
            cas_ticketverify+="?ticket=%s&service=%s" % (ticket, service_full)
            host = urlparse(request.build_absolute_uri()).netloc
            response = requests.get("https://%s%s" % (host, cas_ticketverify))
            logger.info("Response from verify: " + str(response.status_code))
            logger.info("Response from verify: " + response.text)

            # read jwt for identity
            username, decoded_dict = read_jwt(response.text, settings.SECRET_KEY)
            logger.info("Identity from Token: %s" % username)
            logger.info("Identity from Token: %s" % str(decoded_dict))

            user = User.objects.get(username=username)
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            auth_login(request, user)

            request.session['cookie_path'] = "/userland/%s/%s" % (base.user.username, base.name)
            request.session.cycle_key()

            # user is logged in successfully, redirect to service URL
            return HttpResponseRedirect(service)

        # User need to authenticate first on cas
        url = reverse('cas-login')+"?service=%s" % service_full
        logger.info("Redirecting to CAS login %s" % url)
        return HttpResponseRedirect(url)
    return wrapper
