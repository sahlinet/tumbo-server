from re import compile

from django.http import HttpResponseRedirect
from django.conf import settings

from BeautifulSoup import BeautifulSoup

from core.models import Base

EXEMPT_URLS = [compile(settings.LOGIN_URL.lstrip('/'))]
if hasattr(settings, 'LOGIN_EXEMPT_URLS'):
    EXEMPT_URLS += [compile(expr) for expr in settings.LOGIN_EXEMPT_URLS]


class LoginRequiredOrSharedkeyMiddleware:
    def process_request(self, request):
        assert hasattr(request, 'user'), "The Login Required middleware\
 requires authentication middleware to be installed. Edit your\
 MIDDLEWARE_CLASSES setting to insert\
 'django.contrib.auth.middlware.AuthenticationMiddleware'. If that doesn't\
 work, ensure your TEMPLATE_CONTEXT_PROCESSORS setting includes\
 'django.core.context_processors.auth'."
        if not request.user.is_authenticated():
            path = request.path_info.lstrip('/')
            if not any(m.match(path) for m in EXEMPT_URLS):
                assert request.GET.__contains__('shared_key'), "missing shared_key"
                shared_key = request.GET.get('shared_key')
                return
                assert Base.objects.get(uuid=shared_key),  "does not exist"
                return HttpResponseRedirect(settings.LOGIN_URL)


class PrettifyMiddleware(object):
    """HTML code prettification middleware."""
    def process_response(self, request, response):
        if settings.DEBUG and response.status_code is 200 and response['Content-Type'].split(';', 1)[0] == 'text/html':
            response.content = BeautifulSoup(response.content).prettify()
        return response
