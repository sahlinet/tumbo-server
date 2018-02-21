"""
WSGI config for tumbo project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""

import os
import newrelic.agent

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tumbo.settings")

# pylint: disable=C0103
if os.path.exists("/newrelic.ini"):
    newrelic.agent.initialize('/newrelic.ini')
    application = get_wsgi_application()
    application = newrelic.agent.wsgi_application()(application)

else:
    application = get_wsgi_application()