# -*- coding: utf-8 -*-
import zipfile
import requests
from threading import Thread
from rest_framework.renderers import JSONRenderer
from rest_framework_jsonp.renderers import JSONPRenderer
from rest_framework import permissions, viewsets, views
from rest_framework import status

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.conf import settings
from django.db import transaction
from django.core.management import call_command

from rest_framework import renderers
from rest_framework.authentication import SessionAuthentication, TokenAuthentication, BasicAuthentication
from rest_framework.response import Response
#from rest_framework.decorators import link
from rest_framework.exceptions import APIException

from api_authentication import CustomSessionAuthentication

from django.contrib.auth import get_user_model

from core.importer import import_base
from core.models import Base, Apy, Setting, TransportEndpoint, Transaction
from core.api_serializers import PublicApySerializer, ApySerializer, BaseSerializer, SettingSerializer, TransportEndpointSerializer, TransactionSerializer
from core.utils import check_code
from core.views import DjendExecView

User = get_user_model()

import logging
logger = logging.getLogger(__name__)


class ServerConfigViewSet(views.APIView):


    renderer_classes = (JSONRenderer, )

    def get(self, *args, **kwargs):
        data = {'QUEUE_HOST_ADDR': settings.WORKER_RABBITMQ_HOST,
                'QUEUE_HOST_PORT': settings.WORKER_RABBITMQ_PORT,
                'TUMBO_WORKER_THREADCOUNT': settings.TUMBO_WORKER_THREADCOUNT,
                'TUMBO_PUBLISH_INTERVAL': settings.TUMBO_PUBLISH_INTERVAL
        }
        return Response(data)


class SettingViewSet(viewsets.ModelViewSet):
    model = Setting
    serializer_class = SettingSerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication,)
    renderer_classes = [JSONRenderer, JSONPRenderer]

    def get_queryset(self):
        name = self.kwargs['name']
        return Setting.objects.filter(base__user=self.request.user, base__name=name)

    def perform_create(self, serializer):
        base_obj = Base.objects.get(name=self.kwargs['name'], user=self.request.user)
        serializer.save(base=base_obj)


class TransportEndpointViewSet(viewsets.ModelViewSet):
    model = TransportEndpoint
    serializer_class = TransportEndpointSerializer
    authentication_classes = (SessionAuthentication,)

    def get_queryset(self):
        return TransportEndpoint.objects.filter(user=self.request.user)

    def pre_save(self, obj):
        obj.user = self.request.user


class TransactionViewSet(viewsets.ModelViewSet):
    model = Transaction
    serializer_class = TransactionSerializer
    renderer_classes = [JSONRenderer, JSONPRenderer]
    authentication_classes = (TokenAuthentication, SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        name = self.kwargs['name']
        get_object_or_404(Base, user=self.request.user, name=name)
        queryset = Transaction.objects.filter(apy__base__name=name)
        rid = self.request.GET.get('rid', None)
        if rid is not None:
            return queryset.filter(rid=rid)
        return queryset.order_by("modified")[10:]


class ApyViewSet(viewsets.ModelViewSet):
    model = Apy
    serializer_class = ApySerializer
    renderer_classes = [JSONRenderer, JSONPRenderer]
    authentication_classes = (TokenAuthentication, SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Apy.objects.all()

    def get_queryset(self, *args, **kwargs):
        name = self.kwargs['base_name']
        get_object_or_404(Base, user=self.request.user, name=name)
        return Apy.objects.filter(base__user=self.request.user, base__name=name)

    def perform_create(self, serializer):
        base_obj = Base.objects.get(name=self.kwargs['base_name'], user=self.request.user)
        serializer.save(base=base_obj)

    def perform_update(self, serializer):
        # TODO: verify that not a foreign function can be updated
        #obj.base = Base.objects.get(name=self.kwargs['base_name'], user=self.request.user)
        result, warnings, errors = check_code(serializer.initial_data['module'], serializer.instance.name)
        warnings_prep = []
        errors_prep = []
        for warning in warnings:
            warnings_prep.append(
                {
                    'filename': warning.filename,
                    'lineno': warning.lineno,
                    'col': warning.col,
                    'msg': warning.message % warning.message_args,
                })

        for error in errors:
            errors_prep.append(
                {
                    'filename': error.filename,
                    'lineno': error.lineno,
                    'col': error.col,
                    'msg': error.message,
                })
        if not result:
            response_data = {
                'warnings': warnings_prep,
                'errors': errors_prep
            }
            raise APIException(response_data)

        serializer.save()

    def clone(self, request, base_name, name):
        base = get_object_or_404(Base, name=base_name,
                        user=User.objects.get(username=request.user.username))
        clone_count = base.apys.filter(name__startswith="%s_clone" % name).count()
        created = False
        while not created:
            cloned_exec, created = Apy.objects.get_or_create(base=base,
                                name="%s_clone_%s" % (name, str(clone_count+1)))
            clone_count += 1

        cloned_exec.module = base.apys.get(name=name).module
        cloned_exec.save()

        self.object = cloned_exec
        self.kwargs['pk'] = self.object.id
        return self.retrieve(request, new_pk=cloned_exec.id)


class ApyViewSetByName(ApyViewSet):
    lookup_field = ('name')


class ApyExecutionViewSet(viewsets.ModelViewSet):
    model = Apy
    serializer_class = ApySerializer
    renderer_classes = [JSONRenderer, JSONPRenderer]
    #authentication_classes = (TokenAuthentication, SessionAuthentication,)
    authentication_classes = (TokenAuthentication, CustomSessionAuthentication,)

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(ApyExecutionViewSet, self).dispatch(*args, **kwargs)

    def execute(self, request, username, name, apy_name):
        apy_obj = get_object_or_404(Apy, base__user__username=username, name=apy_name, base__name=name)

        kwargs = {
            'base': name,
            'id': apy_obj.id
        }

        # public and owner
        if apy_obj.public or apy_obj.base.user == self.request.user:
            return DjendExecView.as_view()(self.request, **kwargs)

        # shared key
        if request.GET.has_key('shared_key'):
            shared_key = request.GET.get('shared_key', None)
            if apy_obj.base.uuid == shared_key:
                #request.session['shared_key'] = shared_key
                return DjendExecView.as_view()(self.request, **kwargs)
        raise Http404


class CoreApyExecutionViewSet(ApyExecutionViewSet):

    def execute(self, request, name, apy_name):
        username = request.user
        return super(CoreApyExecutionViewSet, self).execute(request, username, name, apy_name)


class PublicApyViewSet(ApyViewSet):
    serializer_class = PublicApySerializer

    def get_queryset(self):
        return Apy.objects.filter(public=True)


class BaseAdminViewSet(viewsets.ModelViewSet):
    model = Base
    serializer_class = BaseSerializer
    renderer_classes = [JSONRenderer, JSONPRenderer]
    authentication_classes = (
        TokenAuthentication,
        SessionAuthentication,
        BasicAuthentication
        )
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser)

    def get_queryset(self):
        return Base.objects.all()._clone().all()

    def destroy_all(self, request):
        logger.info("Destroy all workers")
        thread = Thread(target=call_command, args=('destroy_workers', ))
        thread.start()
        return Response("ok", status=status.HTTP_202_ACCEPTED)

    def recreate_all(self, request):
        logger.info("Recreate all workers")
        thread = Thread(target=call_command, args=('recreate_workers', ))
        thread.start()
        return Response("ok", status=status.HTTP_202_ACCEPTED)


class BaseLogViewSet(viewsets.ViewSet):
    model = Base
    renderer_classes = [JSONRenderer, JSONPRenderer]
    authentication_classes = (
        TokenAuthentication,
        SessionAuthentication,
        BasicAuthentication
        )
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser)

    def log(self, request, name):
        base = Base.objects.get(name=name)
        logs = base.executor.implementation.log(base.executor.pid)
        return Response(logs)


class BaseViewSet(viewsets.ModelViewSet):
    model = Base
    serializer_class = BaseSerializer
    renderer_classes = [JSONRenderer, JSONPRenderer]
    authentication_classes = (TokenAuthentication, SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = 'name'
    queryset = Base.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return Base.objects.all()._clone().filter(user=self.request.user)

    def start(self, request, name):
        with transaction.atomic():
            logger.info("starting %s" % name)
            base = self.get_queryset().select_for_update(nowait=True).get(name=name)
            base.start()
        return self.retrieve(request, name=name)

    def stop(self, request, name):
        with transaction.atomic():
            base = self.get_queryset().select_for_update(nowait=True).get(name=name)
            logger.info("stopping %s" % base.name)
            base.stop()
        return self.retrieve(request, name=name)

    def restart(self, request, name):
        with transaction.atomic():
            logger.info("restarting %s" % name)
            base = self.get_queryset().get(name=name)
            base.stop()
            base.start()
        return self.retrieve(request, name=name)

    def destroy(self, request, name):
        with transaction.atomic():
            logger.info("destroying %s" % name)
            base = self.get_queryset().get(name=name)
            base.stop()
            base.destroy()
        return self.retrieve(request, name=name)

    def recreate(self, request, name):
        with transaction.atomic():
            logger.info("recreate %s" % name)
            base = self.get_queryset().get(name=name)
            base.stop()
            base.destroy()
            base.start()
        return self.retrieve(request, name=name)

    def delete(self, request, name):
        logger.info("delete: %s" % name)
        try:
            base = self.get_queryset().get(name=name)
        except Base.DoesNotExist:
            raise Http404
        base.stop()
        base.destroy()
        base.delete()
        return HttpResponse()

    def transport(self, request, name):
        base = self.get_queryset().get(name=name)
        transport_url = self.request.DATA['url']
        transport_token = self.request.DATA['token']
        zf = base.export()
        zf.seek(0)
        logger.info("Calling "+transport_url)
        logger.info("Token "+transport_token)
        transport = TransportEndpoint.objects.get(
                user=request.user,
                url=transport_url
                )
        r = requests.post(transport_url, headers={
            'Authorization': 'Token '+transport_token
            }, data={
            'name': base.name,
            'override_private': transport.override_settings_priv,
            'override_public': transport.override_settings_pub,
            }, files={
            'file': zf
            }, verify=False)
        logger.info(r.request.headers)
        logger.info((r.status_code))
        logger.info((r.text))

        s = "transport %s" % transport_url
        if r.status_code == 201:
            logger.info("%s success" % s)
            return self.retrieve(request, name=name)
        else:
            logger.error("%s failed with returncode %s" % (s, r.status_code))
            raise Exception("%s failed" % s)

    #@link()
    def apy(self, request, name):
        queryset = Apy.objects.filter(base__name=name)
        serializer = ApySerializer(queryset,
                context={'request': request}, many=True)
        return Response(serializer.data)


class ZipFileRenderer(renderers.BaseRenderer):
    media_type = 'application/zip'
    format = 'zip'

    def render(self, data, media_type=None, renderer_context=None):
        return data


# TODO: the serializer_class is only set to satisfy swagger. We should implement a Serializer, 
class BaseExportViewSet(viewsets.ModelViewSet):
    model = Base
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = [ZipFileRenderer]
    serializer_class = BaseSerializer

    def get_queryset(self):
        return Base.objects.all()._clone().filter(user=self.request.user)

    def export(self, request, name):
        base = self.get_queryset().get(name=name)
        f = base.export()
        logger.info(f)

        response = Response(f.getvalue(), headers={
            'Content-Disposition': 'attachment; filename=%s.zip' % base.name
            }, content_type='application/zip')
        return response


class BaseImportViewSet(viewsets.ModelViewSet):
    model = Base
    authentication_classes = (TokenAuthentication, SessionAuthentication, )
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = BaseSerializer

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(BaseImportViewSet, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        return Base.objects.all()._clone().filter(user=self.request.user)

    def imp(self, request):
        logger.info("start import")
        # Base
        name = request.POST['name']
        override_public = bool(request.GET.get('override_public', False))
        override_private = bool(request.GET.get('override_private', False))

        f = request.FILES['file']
        zf = zipfile.ZipFile(f)

        base = import_base(zf,
                           request.user,
                           name,
                           override_public,
                           override_private)

        base_queryset = base
        base.save()
        serializer = BaseSerializer(base_queryset,
                                    context={'request': request}, many=False)
        response = Response(serializer.data, status=201)
        return response
