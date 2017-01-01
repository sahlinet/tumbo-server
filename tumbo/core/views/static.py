import os
import sys
import base64
import logging
import json
import dropbox

from dropbox.rest import ErrorResponse

from datetime import datetime

from django.contrib.auth import get_user_model
from django.views.generic import View
from django.http import HttpResponseNotFound, HttpResponse, HttpResponseServerError, HttpResponseNotModified
from django.conf import settings
from django.core.cache import cache
from django.template import Template, RequestContext

from core.utils import totimestamp, fromtimestamp
from core.queue import generate_vhost_configuration
from core.models import Base, StaticFile
from core.executors.remote import get_static
from core.plugins.datastore import PsqlDataStore
from core.views import ResponseUnavailableViewMixing
from core.staticfiles import StaticfileFactory, NotFound, StorageStaticFile


User = get_user_model()

logger = logging.getLogger(__name__)


class DjendStaticView(ResponseUnavailableViewMixing, View):

    def _render_html(self, request, t, **kwargs):
        if type(t) == str:
            t = Template(t)
        else:
            #t = Template(t.read())
            t = Template(t)
        c = RequestContext(request, kwargs, processors=None)
        if request.user.is_anonymous():
            c['user'] = None
        else:
            c['user'] = {}
            c['user']['id'] = request.user.authprofile.internalid
            c['user']['username'] = request.user.username
            c['user']['email'] = request.user.email
        return t.render(c)

    def get(self, request, **kwargs):

        username = kwargs['username']
        project = kwargs['base']
        name = kwargs['name']

        static_path = "%s/%s/%s" % (project, "static", name)
        logger.debug("%s GET" % static_path)

        # verify that base exists for user
        base_obj = Base.objects.get(user__username=kwargs['username'], name=kwargs['base'])

        #response = self.verify(request, base_obj)
        #if response:
        #    return response

        last_modified = None

        try:
            file_fact = StaticfileFactory(username, project, name)
            file_obj = file_fact.lookup()
            file = file_obj.content
        except NotFound, e:
            logger.error(e)
            return HttpResponseNotFound("Not found: %s" % static_path)
        except Exception, e:
            logger.error(e)
            raise e

        # default
        mimetype = "text/plain"
        if static_path.endswith('.js'):
            mimetype = "text/javascript"
        elif static_path.endswith('.css'):
            mimetype = "text/css"
        elif static_path.endswith('.json'):
            mimetype = "application/json"
        elif static_path.endswith('.png'):
            mimetype = "image/png"
        elif static_path.endswith('.woff'):
            mimetype = "application/x-font-woff"
        elif static_path.endswith('.woff2'):
            mimetype = "application/font-woff2"
        elif static_path.endswith('.svg'):
            mimetype = "image/svg+xml"
        elif static_path.endswith('.ttf'):
            mimetype = "application/x-font-ttf"
        elif static_path.lower().endswith('.jpg'):
            mimetype = "image/jpeg"
        elif static_path.lower().endswith('.ico'):
            mimetype = "image/x-icon"
        elif static_path.lower().endswith('.html'):
            mimetype = "text/html"
            context_data = self._setup_context(request, base_obj)
            file = self._render_html(request, file, **context_data)
            context_data['datastore'] = None
            context_data = None
        elif static_path.lower().endswith('.map'):
            mimetype = "application/json"
        elif static_path.lower().endswith('.gif'):
            mimetype = "image/gif"
        elif static_path.lower().endswith('.swf'):
            mimetype = "application/x-shockwave-flash"
        else:
            logger.warning("%s: suffix not recognized" % static_path)
            return HttpResponseServerError("Staticfile suffix not recognized")
        logger.info("%s: with '%s'" % (static_path, mimetype))

        return self._handle_cache(static_path, request, mimetype, last_modified, file)

    def _handle_cache(self, static_path, request, mimetype, last_modified, file):
        if 'content="no-cache"' in file:
            logger.debug("Not caching because no-cache present in HTML")
            response = HttpResponse(file, content_type=mimetype)
        else:
            # handle browser caching
            frmt = "%d %b %Y %H:%M:%S"
            try:
                file.seek(0)
            except AttributeError:
                pass
            if_modified_since = request.META.get('HTTP_IF_MODIFIED_SINCE', None)
            if last_modified and if_modified_since:
                if_modified_since_dt = datetime.strptime(if_modified_since, frmt)
                last_modified = last_modified.replace(microsecond=0)
                logger.debug("%s: checking if last_modified '%s' or smaller/equal of if_modified_since '%s'" % (static_path, last_modified, if_modified_since_dt))
                if (last_modified <= if_modified_since_dt):
                    logger.info("%s: 304" % static_path)
                    return HttpResponseNotModified()
            response = HttpResponse(file, content_type=mimetype)
            if last_modified:
                response['Cache-Control'] = "public"
                response['Last-Modified'] = last_modified.strftime(frmt)
            if static_path.endswith("png") or static_path.endswith("css") or static_path.endswith("js") \
                    or static_path.endswith("woff"):
                response['Cache-Control'] = "max-age=120"
            logger.info("%s: 200" % static_path)
        return response


    def _setup_context(self, request, base_obj):
        data = dict((s.key, s.value) for s in base_obj.setting.all())

        data['TUMBO_STATIC_URL'] = "/%s/%s/%s/static/" % ("userland", base_obj.user.username, base_obj.name)

        try:
            logger.debug("Setup datastore for context starting")
            plugin_settings = settings.TUMBO_PLUGINS_CONFIG['core.plugins.datastore']
            data['datastore'] = PsqlDataStore(schema=base_obj.name, keep=False, **plugin_settings)
            logger.debug("Setup datastore for context done")
            logger.debug("Datastore-Size: %s" % data['datastore'].count())
            data['is_authenticated'] = request.user.is_authenticated()
        except KeyError, e:
            logger.error("Setup datastore for context failed")
        updated = request.GET.copy()
        query_params = {}
        for k, v in updated.iteritems():
            query_params[k] = v
        data['QUERY_PARAMS'] = query_params

        return data
