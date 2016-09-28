import time

from django.conf import settings
from django.shortcuts import redirect
from django.utils.cache import patch_vary_headers
from django.utils.http import cookie_date
from django.contrib.sessions.middleware import SessionMiddleware

import logging

logger = logging.getLogger(__name__)

class CasSessionMiddleware(SessionMiddleware):
    """
    Middleware to handle cookie path.
    """

    def _get_cookie_path(self, request):
        cookie_path = None
        if "cas/" in request.path_info:
            cookie_path = "/cas"

        # authorization step for service saved the cookie_path in session
        try:
            if "cookie_path" in request.session:
                cookie_path = request.session.pop('cookie_path')
                logger.info("Got cookie_path %s to use" % cookie_path)
        except AttributeError:
            logger.error("cookie_path missing")

        logger.info("CasSessionMiddleware: _get_cookie_path for URI %s returned SESSION_COOKIE_PATH %s" % (request.path_info, cookie_path))

        return cookie_path or settings.SESSION_COOKIE_PATH

    def process_response(self, request, response):
        """
        If request.session was modified, or if the configuration is to save the
        session every time, save the changes and set a session cookie or delete
        the session cookie if the session has been emptied.
        """
        try:
            accessed = request.session.accessed
            modified = request.session.modified
            empty = request.session.is_empty()
        except AttributeError:
            pass
        else:
            # First check if we need to delete this cookie.
            # The session should be deleted only if the session is entirely empty
            if settings.SESSION_COOKIE_NAME in request.COOKIES and empty:
                response.delete_cookie(settings.SESSION_COOKIE_NAME, domain=settings.SESSION_COOKIE_DOMAIN)
            else:
                if accessed:
                    patch_vary_headers(response, ('Cookie',))
                if (modified or settings.SESSION_SAVE_EVERY_REQUEST) and not empty:
                    if request.session.get_expire_at_browser_close():
                        max_age = None
                        expires = None
                    else:
                        max_age = request.session.get_expiry_age()
                        expires_time = time.time() + max_age
                        expires = cookie_date(expires_time)
                    # Save the session data and refresh the client cookie.
                    # Skip session save for 500 responses, refs #3881.
                    if response.status_code != 500:
                        try:
                            request.session.save()
                        #except UpdateError:
                        except Exception:
                            # The user is now logged out; redirecting to same
                            # page will result in a redirect to the login page
                            # if required.
                            return redirect(request.path)
                        response.set_cookie(
                            settings.SESSION_COOKIE_NAME,
                            request.session.session_key, max_age=max_age,
                            expires=expires, domain=settings.SESSION_COOKIE_DOMAIN,
                            path=self._get_cookie_path(request),
                            secure=settings.SESSION_COOKIE_SECURE or None,
                            httponly=settings.SESSION_COOKIE_HTTPONLY or None,
                        )
                        logger.info("Create session %s for path: %s" % (request.session.session_key, self._get_cookie_path(request)))
        return response
