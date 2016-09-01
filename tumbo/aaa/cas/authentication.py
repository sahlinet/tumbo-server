import logging
import requests

from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.auth import login as auth_login

from core.models import Base
from core.utils import read_jwt
from aaa.cas.views import verify

User = get_user_model()

logger = logging.getLogger(__name__)

def cas_login(function):
    def wrapper(request, *args, **kwargs):
        # logger.debug("authenticate %s" % request.user)
        user=request.user

        # if logged in
        if request.user.is_authenticated():
            logger.debug("user.is_authenticated")
            return function(request, *args, **kwargs)

        base = Base.objects.get(user__username=kwargs['username'], name=kwargs['base'])
        service = reverse('userland-static', args=[kwargs['username'], kwargs['base'], "index.html"])
        url = reverse('cas-login')+"?service=%s" % service

        ticket = request.GET.get("ticket", None)
        if ticket:

            cas_ticketverify=reverse('cas-ticketverify')
            cas_ticketverify+="?ticket=%s&service=%s" % (ticket, service)
            response = requests.get("https://codeanywhere.sahli.net"+cas_ticketverify)
            logger.info("Response from verify: "+str(response.status_code))
            logger.info("Response from verify: "+response.text)

            # read jwt for identity
            username, decoded_dict = read_jwt(response.text, settings.SECRET_KEY)
            logger.info("Identity from Token: %s" % username)
            logger.info("Identity from Token: %s" % str(decoded_dict))

            user = User.objects.get(username=username)
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            auth_login(request, user)

            #if response.status_code == 200:
            #    logger.info("Verify ticket %s for service %s" % (ticket, service))
            request.session['cookie_path'] = "/userland/admin/httptest"
            return HttpResponseRedirect(service)

        logger.info("Redirecting to CAS login %s" % url)

        return HttpResponseRedirect(url)
    return wrapper


