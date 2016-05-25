"""
WSGI config for tumbo project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""

#import os
#import newrelic.agent
#
#from django.core.wsgi import get_wsgi_application
#
#os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tumbo.settings")
#
#newrelic.agent.initialize('/newrelic.ini')
#
#application = get_wsgi_application()
#application = newrelic.agent.wsgi_application()(application)

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tumbo.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
