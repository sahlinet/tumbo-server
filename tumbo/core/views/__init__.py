import logging
import json
import dropbox
import time
import copy
import threading
import re
from StringIO import StringIO

from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views.generic import View, TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseNotFound, HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseServerError, HttpResponsePermanentRedirect
from django.views.generic.base import ContextMixin
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.core import serializers
from django.core.cache import cache


from core.api_serializers import BaseSerializer
from dropbox.rest import ErrorResponse

from core.utils import UnAuthorized, Connection, NoBasesFound, message, create_jwt
from core.queue import generate_vhost_configuration
from core.models import AuthProfile, Base, Apy, Setting, Executor, Process, Thread, Transaction, StaticFile
from core.models import RUNNING, FINISHED
from core import responses
from core.executors.remote import call_rpc_client

from core.importer import _handle_settings, _read_config

from core.plugins import PluginRegistry
from core.threadpool import ThreadPool

User = get_user_model()

logger = logging.getLogger(__name__)

use_plans = False
try:
    from plans.quota import get_user_quota
except ImportError:
    use_plans = False


class CockpitView(TemplateView):

    def get_context_data(self, **kwargs):
        context = super(CockpitView, self).get_context_data(**kwargs)
        qs = Executor.objects.all().order_by('base__name')
        if not self.request.user.is_superuser:
            qs = qs.filter(base__user=self.request.user)
        context['executors'] = qs.order_by('base__name')
        context['process_list'] = Process.objects.all().order_by('-running')
        context['threads'] = Thread.objects.all().order_by('parent__name', 'name')
        context['plugins'] = PluginRegistry().get()
        return context

    def dispatch(self, *args, **kwargs):
        if not self.request.user.is_superuser:
            return HttpResponseNotFound()
        return super(CockpitView, self).dispatch(*args, **kwargs)


class ResponseUnavailableViewMixing():
    def verify(self, request, base_model):
        if not base_model.state:
            response = HttpResponse()
            if "html" is request.META.get('HTTP_ACCEPT', None):
                response.content_type = "text/html"
                response.content = "Content cannot be delivered"
            response.status_code = 503
            return response
        else:
            return None


class DjendMixin(object):

    def connection(self, request):
        logger.debug("Creating connection for %s" % request.user)
        return Connection(request.user.authprofile.dropbox_access_token)


class DjendExecView(View, ResponseUnavailableViewMixing, DjendMixin):
    STATE_OK = "OK"
    STATE_NOK = "NOK"
    STATE_NOT_FOUND = "NOT_FOUND"
    STATE_TIMEOUT = "TIMEOUT"

    def _prepare_request(self, request, exec_model):
        apy_data = serializers.serialize("json", [exec_model],
                                         fields=('base_id', 'name'))
        struct = json.loads(apy_data)
        apy_data = json.dumps(struct[0])

        request_data = {}
        request_data.update({'model': apy_data,
                             'base_name': exec_model.base.name})
        get_dict = copy.deepcopy(request.GET)
        post_dict = copy.deepcopy(request.POST)
        for key in ["json", "shared_key"]:
            if request.method == "GET":
                if key in get_dict:
                    del get_dict[key]
            if request.method == "POST":
                if key in post_dict:
                    del get_dict[key]
        token = create_jwt(request.user, exec_model.base.executor.secret)
        request_data.update({'request': {
                'method': request.method,
                'content_type': request.META.get('Content-Type'),
                'GET': get_dict.dict(),
                'POST': post_dict.dict(),
                'UUID': exec_model.base.uuid,
                'REMOTE_ADDR': request.META.get('REMOTE_ADDR'),
                'token': token
            }
            })
        logger.debug("REQUEST-data: %s" % request_data)
        return request_data

    def _execute(self, request, request_data, base_model, rid):
        try:
            # _do on remote
            start = int(round(time.time() * 1000))
            request_data.update({'rid': rid})
            response_data = call_rpc_client(json.dumps(request_data),
                generate_vhost_configuration(
                    base_model.user.username,
                    base_model.name),
                    base_model.name,
                    base_model.executor.password
                    )
            end = int(round(time.time() * 1000))
            ms=str(end-start)

            logger.debug("DATA: %s" % str(response_data))

            logger.debug("RESPONSE-time: %sms" %  str(ms))
            logger.debug("RESPONSE-data: %s" % response_data[:120])
            data = json.loads(response_data)
            data.update({
                "time_ms": ms,
            })
        except Exception, e:
            logger.exception(e)
            raise Exception("Could not execute request")
        return data

    def _execute_async(self, request, request_data, base_model, rid):
        try:
            # _do on remote
            request_data.update({'rid': rid})
            call_rpc_client(json.dumps(request_data),
                generate_vhost_configuration(
                    base_model.user.username,
                    base_model.name),
                    base_model.name,
                    base_model.executor.password,
                    async=True
                    )
        except Exception, e:
            logger.exception(e)
            raise e
        return True

    def _handle_response(self, request, data, exec_model):
        response_class = data.get("response_class", None)
        default_status_code = 200
        logger.debug(data)
        if not data.has_key('returned'):
            response_status_code = default_status_code
        else:
            if response_class:
		try:
                	response_status_code = json.loads(data['returned']).get('status_code', default_status_code)
		except:
                	response_status_code = data['returned'].get('status_code', default_status_code)
            else:
                response_status_code = default_status_code

        # respond with json
        if request.GET.has_key(u'json') or request.GET.has_key('callback'):
            status = data.get("status", False)
	    # if is json
            if status == "OK":
                exec_model.mark_executed()
            else:
                exec_model.mark_failed()

            if status in [self.STATE_NOK]:
                response_status_code = 500
            elif status in [self.STATE_NOT_FOUND]:
                response_status_code = 404
            elif status in [self.STATE_TIMEOUT]:
                response_status_code = 502

            # send counter to client
            # cdata = {
            #    'counter':
            #        {
            #        'executed': str(Apy.objects.get(id=exec_model.id).counter.executed),
            #        'failed': str(Apy.objects.get(id=exec_model.id).counter.failed)
            #        },
            #    'apy_id': exec_model.id
            # }

            if request.GET.has_key('callback'):
                data = '%s(%s);' % (request.REQUEST['callback'], json.dumps(data))
                return HttpResponse(data, "application/javascript")
            return HttpResponse(json.dumps(data), content_type="application/json", status=response_status_code)

        # real response
        elif response_class:
            if response_class == u''+responses.XMLResponse.__name__:
                content_type = load_json(data['returned'])['content_type']
                content = load_json(data['returned'])['content']
            elif response_class == u''+responses.HTMLResponse.__name__:
                content_type = load_json(data['returned'])['content_type']
                content = load_json(data['returned'])['content']
            elif response_class == u''+responses.JSONResponse.__name__:
                content_type = load_json(data['returned'])['content_type']
                content = load_json(data['returned'])['content']
            elif response_class == u''+responses.RedirectResponse.__name__:
                location = load_json(data['returned'])['content']
                return HttpResponseRedirect(location)
            else:
                logger.warning("Wrong response")
                return HttpResponseServerError("You're apy did not return any allowed response-class or is not called with 'json' or 'callback' as querystring.")

            return HttpResponse(content, content_type, status=response_status_code)

        else:
            msg = "Not received json or callback query string nor response_class from response."
            logger.error("Not received json or callback query string nor response_class from response.")
            return HttpResponseServerError(msg)

    #@profile
    @never_cache
    def get(self, request, *args, **kwargs):
        # get base
        base_model = get_object_or_404(Base, name=kwargs['base'])

        response = self.verify(request, base_model)
        if response:
            return response
        # get exec from database
        try:
            exec_model = base_model.apys.get(id=kwargs['id'])
        except Apy.DoesNotExist:
            return HttpResponseNotFound("'%s' not found"     % request.META['PATH_INFO'])

        rid = request.GET.get('rid', None)
        if rid:
            # look for transaction
            transaction = Transaction.objects.get(pk=rid)
            if transaction.tout:
                data = transaction.tout
            else:
                data = {'status': transaction.get_status_display()}
                redirect_to = request.get_full_path()
                data.update({'url': redirect_to})
        else:
            request_data = self._prepare_request(request, exec_model)
            transaction = Transaction(apy=exec_model)
            transaction.tin = json.dumps(request_data)
            transaction.status = RUNNING
            transaction.save()

            if request.GET.has_key('async') or request.POST.has_key('async'):
                transaction.async = True
                transaction.save()
                # execute async
                data = self._execute_async(request, request_data, base_model, transaction.rid)
                redirect_to = request.get_full_path()+"&rid=%s" % transaction.rid
                return HttpResponsePermanentRedirect(redirect_to)
            else:
                # execute
                data = self._execute(request, request_data, base_model, transaction.rid)

		try:
			returned = json.loads(data['returned'])
			data['returned'] = returned
		except Exception:
			logger.exception("returned data could not be loaded")
                transaction.tout = json.dumps(data)
                transaction.status = FINISHED
                transaction.save()

        # add exec's id to the response dict
        data.update({
            "id": kwargs['id'],
            "rid": transaction.rid
            })

        # response
        response = self._handle_response(request, data, exec_model)
        if response and data.get('returned', None):
            if not request.GET.get('async', False) and "action" in data['returned'] and data['returned']['action'] == "RESTART":
                logger.info("Restarting base %s" % base_model.name)
                base_model.stop()
                base_model.start()
        return response


    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        return DjendExecView.get(self, request, *args, **kwargs)

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(DjendExecView, self).dispatch(*args, **kwargs)


class DjendSharedView(View, ContextMixin):

    def get(self, request, *args, **kwargs):
        context = RequestContext(request)
        base_name = kwargs.get('base')
        shared_key = request.GET.get('shared_key')

        if not shared_key:
            shared_key = request.session.get('shared_key')

        base_model = get_object_or_404(Base, name=base_name, uuid=shared_key)
        # store it in session list
        if not request.session.__contains__('shared_bases'):
            request.session['shared_bases'] = {}
        request.session['shared_bases'][base_name] = shared_key
        request.session.modified = True

        # context
        context['VERSION'] = version
        context['shared_bases'] = request.session['shared_bases']
        context['TUMBO_EXECS'] = base_model.apys.all().order_by('name')
        context['LAST_EXEC'] = request.GET.get('done')
        context['active_base'] = base_model
        context['username'] = request.user.username
        context['TUMBO_NAME'] = base_model.name
        context['TUMBO_STATIC_URL'] = "/%s/%s/static/" % ("fastapp", base_model.name)

        rs = base_model.template(context)
        return HttpResponse(rs)


class DjendBaseCreateView(View):

    def post(self, request, *args, **kwargs):

        if use_plans:
            if get_user_quota(request.user).get('MAX_BASES_PER_USER') <= request.user.bases.count():
                return HttpResponseForbidden("Too many bases for your plan.")

        base, created = Base.objects.get_or_create(name=request.POST.get('new_base_name'), user=User.objects.get(username=request.user.username))
        if not created:
            return HttpResponseBadRequest("A base with this name does already exist.")
        base.save_and_sync()
        base_data = BaseSerializer(base)
        response_data = base_data.data
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(DjendBaseCreateView, self).dispatch(*args, **kwargs)

class DjendBaseDeleteView(View):

    def post(self, request, *args, **kwargs):
        base = Base.objects.get(name=kwargs['base'], user=request.user)
        base.delete()
        response_data = {"redirect": "/core/dashboard/"}
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(DjendBaseDeleteView, self).dispatch(*args, **kwargs)


class DjendBaseSettingsView(View):

    def get(self, request, *args, **kwargs):
        base = Base.objects.get(name=kwargs['base'])
        base_settings = base.setting.all().extra(\
            select={'lower_key':'lower(key)'}).order_by('lower_key').values('key', 'value', 'id')
        return HttpResponse(json.dumps(list(base_settings)), content_type="application/json")

    def delete(self, request, *args, **kwargs):
        base = Base.objects.get(name=kwargs['base'])
        base_setting = base.setting.get(id=kwargs['id'])
        base_setting.delete()
        return HttpResponse(content_type="application/json")

    def post(self, request, *args, **kwargs):
        base_settings = json.loads(request.POST.get('settings'))
        try:
            for setting in base_settings:
                base = Base.objects.get(name=kwargs['base'])
                if setting.has_key('id'):
                    setting_obj = Setting.objects.get(base=base, id=setting['id'])
                    setting_obj.key = setting['key']
                else:
                    setting_obj = Setting(key=setting['key'], base=base)
                setting_obj.value = setting['value']
                setting_obj.save()
        except Exception:
            logger.exception()
        return HttpResponse({}, content_type="application/json")

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(DjendBaseSettingsView, self).dispatch(*args, **kwargs)


class DjendExecDeleteView(View):

    def post(self, request, *args, **kwargs):
        base = get_object_or_404(Base, name=kwargs['base'], user=User.objects.get(username=request.user.username))

        # syncing to storage provider
        # exec
        e = base.apys.get(name=kwargs['id'])
        try:
            e.delete()
            #info(request.user.username, "Exec '%s' deleted" % e.exec_name)
        except Exception, e:
            pass
            #error(request.user.username, "Error deleting(%s)" % e)
        return HttpResponse('{"redirect": %s}' % request.META['HTTP_REFERER'])

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(DjendExecDeleteView, self).dispatch(*args, **kwargs)


    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(DjendExecRenameView, self).dispatch(*args, **kwargs)


class DjendBaseRenameView(View):

    def post(self, request, *args, **kwargs):
        base = get_object_or_404(Base, name=kwargs['base'], user=User.objects.get(username=request.user.username))
        base.name = request.POST.get('new_name')
        base.save()
        response_data = {"redirect": request.META['HTTP_REFERER'].replace(kwargs['base'], base.name)}
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(DjendBaseRenameView, self).dispatch(*args, **kwargs)


class DjendBaseSaveView(View):

    def post(self, request, *args, **kwargs):
        base = get_object_or_404(Base, name=kwargs['base'], user=User.objects.get(username=request.user.username))
        content = request.POST.get('content', None)
        public = request.POST.get('public', None)
        static_public = request.POST.get('static_public', None)

        # exec
        if request.POST.has_key('exec_name'):
            exec_name = request.POST.get('exec_name')
            # save in database
            e = base.apys.get(name=exec_name)
            if len(content) > 8200:
                pass
            else:
                e.module = content
                e.description = request.POST.get('exec_description')
                e.save()
        # base
        else:
            logger.info("Save base")
            if content: base.content = content
            import distutils
            if public: base.public = distutils.util.strtobool(public)
            if static_public: base.static_public = distutils.util.strtobool(static_public)
            base.save()

        return HttpResponse()

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(DjendBaseSaveView, self).dispatch(*args, **kwargs)


class DjendBaseView(TemplateView, ContextMixin):

    def _refresh_single_base(self, base):
        base = Base.objects.get(name=base)
        base.refresh()
        base.save()

    def get(self, request, *args, **kwargs):
        rs = None
        context = RequestContext(request)

        # redirect to shared view
        if not request.user.is_authenticated():
            if request.GET.has_key('shared_key') or request.session.__contains__("shared_key"):
                return DjendSharedView.as_view()(request, *args, **kwargs)

        try:
            # refresh bases from dropbox
            refresh = "refresh" in request.GET

            base = kwargs.get('base')

            if refresh and base:
                self._refresh_single_base(base)

            base_model = None
            if base:
                base_model = get_object_or_404(Base, name=base, user=request.user.id)
                #base_model.save()
                #if refresh:
                #    base_model.refresh_execs()

                # execs
                try:
                    context['TUMBO_EXECS'] = base_model.apys.all().order_by('name')
                except ErrorResponse, e:
                    messages.warning(request, "No app.json found", extra_tags="alert-warning")
                    logging.debug(e)

            # context
            try:
                context['bases'] = Base.objects.filter(user=request.user.id).order_by('name')
                context['TUMBO_NAME'] = base
                #context['DROPBOX_REDIRECT_URL'] = settings.DROPBOX_REDIRECT_URL
                #context['PUSHER_KEY'] = settings.PUSHER_KEY
                context['TUMBO_STATIC_URL'] = "/%s/%s/static/" % ("fastapp", base)
                context['active_base'] = base_model
                context['username'] = request.user.username
                context['LAST_EXEC'] = request.GET.get('done')
                context['transaction_list'] = Transaction.objects.filter(apy__base__name=base).filter(created__gte=datetime.now()-timedelta(minutes=30)).order_by('created')
                #rs = base_model.template(context)

            except ErrorResponse, e:
                if e.__dict__['status'] == 404:
                    logging.debug(base)
                    logging.debug("Template not found")
                    messages.error(request, "Template %s not found" % template_name, extra_tags="alert-danger")

        # error handling
        except (UnAuthorized, AuthProfile.DoesNotExist), e:
            return HttpResponseRedirect("/fastapp/dropbox_auth_start")
        except NoBasesFound, e:
            message(request, logging.WARNING, "No bases found")

        rs = render_to_string("fastapp/base.html", context_instance=context)
        #rs = render_to_string("fastapp/base.html", context_instance=context)

        return HttpResponse(rs)


class DjendView(TemplateView):

    def get_context_data(self, **kwargs):
        context = super(DjendView, self).get_context_data(**kwargs)
        context['bases'] = Base.objects.filter(user=self.request.user).order_by('name')
        context['public_bases'] = Base.objects.filter(public=True).order_by('name')

        #try:
        #    token = self.request.user.auth_token
        #except Token.DoesNotExist:
        #    token = Token.objects.create(user=self.request.user)
        #context['TOKEN'] = token
        return context

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DjendView, self).dispatch(*args, **kwargs)


def get_dropbox_auth_flow(web_app_session):
    redirect_uri = "%s/fastapp/dropbox_auth_finish" % settings.DROPBOX_REDIRECT_URL
    dropbox_consumer_key = settings.DROPBOX_CONSUMER_KEY
    dropbox_consumer_secret = settings.DROPBOX_CONSUMER_SECRET
    return dropbox.client.DropboxOAuth2Flow(dropbox_consumer_key, dropbox_consumer_secret, redirect_uri, web_app_session, "dropbox-auth-csrf-token")


# URL handler for /dropbox-auth-start
def dropbox_auth_start(request):
    authorize_url = get_dropbox_auth_flow(request.session).start()
    return HttpResponseRedirect(authorize_url)


# URL handler for /dropbox-auth-finish
def dropbox_auth_finish(request):
    try:
        dropbox_access_token, user_id, url_state = get_dropbox_auth_flow(request.session).finish(request.GET)
        auth, created = AuthProfile.objects.get_or_create(user=request.user)
        # store dropbox_access_token
        auth.dropbox_access_token = dropbox_access_token
        auth.dropbox_userid = user_id
        auth.user = request.user
        auth.save()

        return HttpResponseRedirect("/profile/")
    except dropbox.client.DropboxOAuth2Flow.BadRequestException, e:
        return HttpResponseBadRequest(e)
    except dropbox.client.DropboxOAuth2Flow.BadStateException, e:
        # Start the auth flow again.
        return HttpResponseRedirect("http://www.mydomain.com/dropbox_auth_start")
    except dropbox.client.DropboxOAuth2Flow.CsrfException, e:
        return HttpResponseForbidden()
    except dropbox.client.DropboxOAuth2Flow.NotApprovedException, e:
        raise e
    except dropbox.client.DropboxOAuth2Flow.ProviderException, e:
        raise e

# URL handler for /dropbox-auth-start
def dropbox_auth_disconnect(request):
    request.user.authprofile.dropbox_access_token = ""
    request.user.authprofile.save()
    return HttpResponseRedirect("/profile/")


def process_file(path, metadata, client, user):

    def get_app_config(client, path):
        appconfig_file = StringIO()
        appconfig_file = StringIO()
        appconfig_file.write(client.get_file_content(path))
        appconfig_file.seek(0)
        appconfig = _read_config(appconfig_file)
        appconfig_file.close()
        return appconfig

    try:

        # Handle only files ending with ".py" or "config"
        #if not path.endswith("py") or not metadata or "/." in path or not path.endswith("config") or not path is "index.html":
        #    logger.info("Ignore path: %s" % path)
        #    continue

        # setup recognition
        regex = re.compile(".*?\/(.*?)\/(.*?)\/(.*)")
        r = regex.search(path)
        if not r:
            logger.warn("regex '/(.*)/(.*).py' no results in '%s'" % path)
            return
        names = r.groups()
        base_name = names[1]
        try:
            base_obj = Base.objects.get(name=base_name, user=user)
        except:
            logger.warn("Base for %s %s not found" % (user, base_name))
        appconfig_path = "%s/app.config" % base_name
        logger.info("notification for: base_name: %s, user: %s" % (base_name, user))

        if "/." in path:
            logger.debug("Ignore file starting with a dot")
            return

        # Handle app.config
        elif "app.config" in path:
            appconfig = get_app_config(client, path)
            logger.debug("Read app.config for base %s" % base_name)
            # base
            base_obj, created = Base.objects.get_or_create(name=base_name, user=user)
            base_obj.save()
            logger.debug("base %s created?: %s" % (base_name, created))
            # settings
            _handle_settings(appconfig['settings'], base_obj)

        # Handle index.html
        elif path is "index.html":
            index_html = client.get_file_content(path)
            base_obj.content = index_html
            base_obj.save()

        # Handle apys
        elif path.endswith("py"):
            logger.info("Try to handle apy on path %s" % path)
            regex = re.compile("/(.*)/([a-zA-Z-_0-9.]*).py")
            r = regex.search(path)
            apy_name = r.groups()[1]
            try:
                base_obj = Base.objects.get(name=base_name, user=user)
                apy, created = Apy.objects.get_or_create(name=apy_name, base=base_obj)
                if created:
                    apy.save()
                    logger.info("new apy %s created" % apy_name)
                logger.debug("apy %s already exists" % apy_name)
            except Apy.DoesNotExist, e:
                logger.warn(e.message)
                return

            try:
                description = get_app_config(client, appconfig_path)['modules'][apy_name].get('description', None)
                if description:
                    apy.description = get_app_config(client, appconfig_path)['modules'][apy_name]['description']
                    apy.save()
            except Exception, e:
                logger.warn("Description could not be read for %s: %s" % (apy_name, repr(e)))

            new_rev = metadata['rev']
            logger.debug("local rev: %s, remote rev: %s" % (apy.rev, new_rev))

            if apy.rev == new_rev:
                logger.debug("No changes in %s" % path)
            else:
                logger.info("Load changes for %s" % path)

                content, rev = client.get_file_content_and_rev("%s" % path)
                apy.module = content
                logger.info("Update content for %s with %s" % (path, str(len(content))))
                apy.rev = rev
                apy.save()
                logger.info("Apy %s updated" % apy.name)
        else:
            logger.warn("Handling staticfile %s" % path)
            if "static" in path:

                path_orig = path
                path = re.search('\/.*?\/(.*)', path).group(1)
                content, rev = client.get_file_content_and_rev("%s" % path_orig)
                obj, created = StaticFile.objects.get_or_create(base=base_obj, name=path, storage="DR")
                if obj.rev != rev or created:
                    obj.rev = rev
                    obj.save()
                try:
                    cache_path = path.lstrip("/")
                    base_obj = Base.objects.get(name=base_name, user=user)
                    cache_key = "%s-%s-%s" % (base_obj.user.username, base_obj.name, cache_path)
                    logger.debug("Delete cache entry: %s" % cache_key)
                    cache.delete(cache_key)


                except Exception, e:
                    logger.error("Problem cleaning cache for static file %s" % cache_path)
                    logger.warn("Looking for %s for user %s" % (base_name, user.username))

    except Exception, e:
        logger.error("Exception handling path %s" % path)
        logger.exception(e)


def process_user(uid):
    auth_profile = AuthProfile.objects.filter(dropbox_userid=uid)[0]
    token = auth_profile.dropbox_access_token
    user = auth_profile.user
    logger.info("START process user '%s'" % user)
    logger.debug("Process change notfication for user: %s" % user.username)
    cursor = cache.get("cursor-%s" % uid)

    client = Connection(token)

    has_more = True
    while has_more:
        result = client.delta(cursor)

        pool = ThreadPool(1)
        for path, metadata in result['entries']:
            logger.info("Add task for %s to pool" % path)
            pool.add_task(process_file, path, metadata, client, user)
            logger.debug("Waiting for completion ... %s" % path)
        pool.wait_completion()
        logger.debug("Tasks completed.")

        # Update cursor
        cursor = result['cursor']
        cursor = cache.set("cursor-%s" % uid, cursor)

        # Repeat only if there's more to do
        has_more = result['has_more']

    logger.info("END process user '%s'" % user)


class DropboxNotifyView(View):

    def get(self, request):
        try:
            challenge = request.GET['challenge']
        except:
            logger.warn("DropboxNotifyView called without challenge")
            return HttpResponseNotFound("Not Found")
        return HttpResponse(challenge)

    def post(self, request):
        logger.info("DropboxNotifyView is called")

        # get delta for user
        for uid in json.loads(request.body)['delta']['users']:
            logger.debug("Start thread for handling delta for user '%s'" % uid)
            thread = threading.Thread(target=process_user, args=(uid,))
            thread.daemon = True
            thread.start()

        return HttpResponse()

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(DropboxNotifyView, self).dispatch(*args, **kwargs)


@csrf_exempt
def login_or_sharedkey(function):
    def wrapper(request, *args, **kwargs):
        # logger.debug("authenticate %s" % request.user)
        user=request.user

        # if logged in
        if user.is_authenticated():
            return function(request, *args, **kwargs)

        base_name = kwargs.get('base')
        base_obj = get_object_or_404(Base, name=base_name)

        # static_public
        if "static" in request.path_info and base_obj.static_public:
            return function(request, *args, **kwargs)

        # if base is public
        if base_obj.public:
           return function(request, *args, **kwargs)

        # if shared key in query string
        elif request.GET.has_key('shared_key'):
            shared_key = request.GET.get('shared_key', None)
            if base_obj.uuid==shared_key or base_obj.public:
                request.session['shared_key'] = shared_key
                return function(request, *args, **kwargs)
            else:
                return HttpResponseNotFound()
        # if shared key in session and corresponds to base
        #has_shared_key = request.session.__contains__('shared_key')
        #if has_shared_key:
        #    shared_key = request.session['shared_key']
        #    logger.info("authenticate on base '%s' with shared_key '%s'" % (base, shared_key))
        #    get_object_or_404(Base, name=base_name, uuid=shared_key)
        #    return function(request, *args, **kwargs)
        # don't redirect when access a exec withoud secret key
        elif kwargs.has_key('id'):
            if Apy.objects.get(base=base_obj, id=kwargs['id']).everyone:
                return function(request, *args, **kwargs)
            else:
                return HttpResponseNotFound('Ups, wrong URL?')
        # TODO: should redirect to a nice login page
        return HttpResponseRedirect("/")
    return wrapper

def load_json(s):
    if type(s) is str:	
        r= json.loads(s)
    elif type(s) is dict:
        r = s
    return r

@login_required
def change_password(request):

    if request.is_ajax():
        try:
            # extract new_password value from POST/JSON here, then

            user = User.objects.get(username=request.user.username)
        except User.DoesNotExist:
            return HttpResponse(status = 400)
        else:
            password1 = request.POST['password1']
            password2 = request.POST['password2']
            if password1 == password2 and len(password1) > 8:
                user.set_password(password1)
                user.save()
            else:
                return HttpResponse("Password could not be changed (mininum l", status = 400)

        return HttpResponse("OK")
    else:
        return HttpResponse(status = 400)
