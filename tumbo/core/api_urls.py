from django.conf.urls import patterns, url
from django.views.decorators.csrf import csrf_exempt
from rest_framework import routers
from rest_framework_swagger.views import get_swagger_view

from core.api_views import BaseAdminViewSet, BaseViewSet, BaseLogViewSet, SettingViewSet, PublicApyViewSet, ApyViewSet, BaseExportViewSet, BaseImportViewSet, TransportEndpointViewSet, TransactionViewSet, ApyExecutionViewSet, CoreApyExecutionViewSet, ApyViewSetByName, BaseUpdateViewSet, WebhookView

# Routers provide an easy way of automatically determining the URL conf
router = routers.DefaultRouter(trailing_slash=True)
router.register(r'apy', ApyViewSet)
router.register(r'base', BaseViewSet)

urlpatterns = patterns('',

    # api
    url(r'^transportendpoints/$', TransportEndpointViewSet.as_view({'get': 'list', 'post': 'create'}), name='transportendpoint-list'),
    url(r'^transportendpoints/(?P<pk>\d+)/$', TransportEndpointViewSet.as_view({'put': 'update'}), name='transportendpoint-list'),
    url(r'^base/$', BaseViewSet.as_view({'get': 'list', 'post': 'create'}), name='base-list'),

    # Import / Update
    url(r'^base/import/$', csrf_exempt(BaseImportViewSet.as_view({'post': 'imp'})), name='base-import'),
    url(r'^username/(?P<username>[\w-]+)/base/(?P<name>[\w-]+)/hook/$', csrf_exempt(WebhookView.as_view({'post': 'hook'})), name='base-update-hook'),
    url(r'^base/(?P<name>[\w-]+)/update/$', csrf_exempt(BaseUpdateViewSet.as_view({'post': 'update'})), name='base-update'),

    # Base REST
    url(r'^base/(?P<name>[\w-]+)/$', BaseViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='base-detail'),
    #url(r'^config/$', ServerConfigViewSet.as_view(), name='settings'),

    # Base admin actions
    url(r'^base/destroy_all/$', BaseAdminViewSet.as_view({'get': 'destroy_all'}), name='bases-destroy'),
    url(r'^base/recreate_all/$', BaseAdminViewSet.as_view({'get': 'recreate_all'}), name='bases-recreate'),

    # Base actions
    url(r'^base/(?P<name>[\w-]+)/start/$', BaseViewSet.as_view({'post': 'start'}), name='base-start'),
    url(r'^base/(?P<name>[\w-]+)/stop/$', BaseViewSet.as_view({'post': 'stop'}), name='base-start'),
    url(r'^base/(?P<name>[\w-]+)/log/$', BaseLogViewSet.as_view({'get': 'log'}), name='base-log'),
    url(r'^base/(?P<name>[\w-]+)/restart/$', BaseViewSet.as_view({'post': 'restart'}), name='base-restart'),
    url(r'^base/(?P<name>[\w-]+)/destroy/$', BaseViewSet.as_view({'post': 'destroy'}), name='base-destroy'),
    url(r'^base/(?P<name>[\w-]+)/recreate/$', BaseViewSet.as_view({'post': 'recreate'}), name='base-recreate'),
    url(r'^base/(?P<name>[\w-]+)/export/$', BaseExportViewSet.as_view({'get': 'export'}), name='base-export'),
    url(r'^base/(?P<name>[\w-]+)/transport/$', BaseViewSet.as_view({'post': 'transport'}), name='base-transport'),
    url(r'^base/(?P<name>[\w-]+)/delete/$', BaseViewSet.as_view({'post': 'delete'}), name='base-delete'),

    url(r'^base/(?P<base_name>[\w-]+)/apy/$', ApyViewSet.as_view({'get': 'list', 'post': 'create'}), name='apy-list'),
    url(r'^base/(?P<base_name>[\w-]+)/apy/(?P<name>[\w-]+)/$', ApyViewSetByName.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='apy-detail2'),

    url(r'^base/(?P<base_name>[\w-]+)/apy/(?P<pk>\d+)/$', ApyViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='apy-detail'),

    url(r'^public-apy/$', PublicApyViewSet.as_view({'get': 'list'}), name='public-apy-list'),
    url(r'^public-apy/(?P<pk>\d+)/$', PublicApyViewSet.as_view({'get': 'retrieve'}), name='public-apy-detail'),
    # Apy CRUD operations
    url(r'^base/(?P<base_name>[\w-]+)/apy/(?P<name>[\w-]+)/clone/$', ApyViewSet.as_view({'post': 'clone'}), name='apy-clone'),
    url(r'^username/(?P<username>[\w-]+)/base/(?P<name>[\w-]+)/apy/(?P<apy_name>[\w-]+)/execute/$', ApyExecutionViewSet.as_view({'post': 'execute', 'get': 'execute'}), name='apy-public-exec'),
    url(r'^base/(?P<name>[\w-]+)/apy/(?P<apy_name>[\w-]+)/execute/$', CoreApyExecutionViewSet.as_view({'post': 'execute', 'get': 'execute'}), name='apy-exec'),
    url(r'^base/(?P<name>[\w-]+)/setting/$', SettingViewSet.as_view({'get': 'list', 'post': 'create'}), name='apy-list'),
    url(r'^base/(?P<name>[\w-]+)/setting/(?P<pk>\d+)/$', SettingViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='apy-detail'),
    url(r'^base/(?P<name>[\w-]+)/transactions/$', TransactionViewSet.as_view({'get': 'list'}), name='transaction-list'),

    # api-authtoken
    url(r'^api-token-auth/', 'rest_framework.authtoken.views.obtain_auth_token'),

    # api-docs
    url(r'^api-docs', get_swagger_view(title='Tumbo API'), name='api-docs')
)

from rest_framework.urlpatterns import format_suffix_patterns
urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'api'])
