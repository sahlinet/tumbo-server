from corsheaders.middleware import CorsMiddleware
from corsheaders.middleware import CorsPostCsrfMiddleware
from rest_framework.authentication import SessionAuthentication
from rest_framework import exceptions

from django.middleware.csrf import CsrfViewMiddleware

# From https://github.com/tomchristie/django-rest-framework/issues/2982

class CustomCSRFCheck(CorsMiddleware, CsrfViewMiddleware,
                              CorsPostCsrfMiddleware):
    def _reject(self, request, reason):
        # Return the failure reason instead of an HttpResponse
        return reason

class CustomSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        """
        Enforce CSRF validation for session based authentication.
        """
        reason = CustomCSRFCheck().process_view(request, None, (), {})
        if reason:
                # CSRF failed, bail with explicit error message
                raise exceptions.PermissionDenied('CSRF Failed: %s' % reason)

