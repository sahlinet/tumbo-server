from django.conf.urls import patterns, url, include
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from core.views import DjendBaseView, DjendBaseDeleteView, \
        DjendBaseSaveView, \
        DjendBaseCreateView, \
        DjendExecDeleteView, \
        DjendExecView, \
        login_or_sharedkey, dropbox_auth_finish, dropbox_auth_start, dropbox_auth_disconnect, DjendView, \
        DjendBaseRenameView, CockpitView, DropboxNotifyView, \
        change_password
from core.views.static import DjendStaticView
from rest_framework import routers

#from core.api_views import BaseAdminViewSet, BaseViewSet, BaseLogViewSet, SettingViewSet, PublicApyViewSet, ApyViewSet, BaseExportViewSet, BaseImportViewSet, TransportEndpointViewSet, ServerConfigViewSet
from core.api_views import BaseAdminViewSet, BaseViewSet, BaseLogViewSet, SettingViewSet, PublicApyViewSet, ApyViewSet, BaseExportViewSet, BaseImportViewSet, TransportEndpointViewSet, TransactionViewSet, ApyExecutionViewSet, ApyPublicExecutionViewSet

from django.views.decorators.cache import never_cache

# Routers provide an easy way of automatically determining the URL conf
router = routers.DefaultRouter(trailing_slash=True)
router.register(r'apy', ApyViewSet)
router.register(r'base', BaseViewSet)

urlpatterns = patterns('',

    # dropbox auth
    url(r'dropbox_auth_start/?$',dropbox_auth_start),
    url(r'dropbox_auth_finish/?$',dropbox_auth_finish),
    url(r'dropbox_auth_disconnect/?$',dropbox_auth_disconnect),
    url(r'dropbox_notify/?$', DropboxNotifyView.as_view()),

    url(r'change_password/?$', change_password, name="change_password"),

    url(r'cockpit/$', login_required(never_cache(CockpitView.as_view(template_name="fastapp/cockpit.html"))), name='cockpit'),

    # base
    url(r'(?P<base>[\w-]+)/index/$', login_required(DjendBaseView.as_view(template_name="fastapp/base.html"))),
    url(r'(?P<base>[\w-]+)/sync/$', login_required(DjendBaseSaveView.as_view())),
    url(r'(?P<base>[\w-]+)/new/$', login_required(DjendBaseCreateView.as_view())),
    url(r'(?P<base>[\w-]+)/delete/$', login_required(DjendBaseDeleteView.as_view())),
    url(r'(?P<base>[\w-]+)/rename/$', login_required(DjendBaseRenameView.as_view())),

    # execs
    url(r'(?P<base>[\w-]+)/exec/(?P<id>\d+)/$', \
                                            csrf_exempt(login_or_sharedkey(DjendExecView.as_view())), name='exec'),
    url(r'(?P<base>[\w-]+)/delete/(?P<id>\w+)/$', \
                                            login_required(DjendExecDeleteView.as_view())),

    # static
    url(r'(?P<base>[\w-]+)/static/(?P<name>.+)$', \
                                            login_or_sharedkey(DjendStaticView.as_view())),
    # api
    url(r'^api/transportendpoints/$', TransportEndpointViewSet.as_view({'get': 'list', 'post': 'create'}), name='transportendpoint-list'),
    url(r'^api/transportendpoints/(?P<pk>\d+)/$', TransportEndpointViewSet.as_view({'put': 'update'}), name='transportendpoint-list'),
    url(r'^api/base/$', BaseViewSet.as_view({'get': 'list', 'post': 'create'}), name='base-list'),

    url(r'^api/base/import/$', csrf_exempt(BaseImportViewSet.as_view({'post': 'imp'})), name='base-import'),

    # Base CRUD operations
    url(r'^api/base/(?P<name>[\w-]+)/$', BaseViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='base-detail'),

    #url(r'^api/config/$', ServerConfigViewSet.as_view(), name='settings'),

    url(r'^api/base/destroy_all/$', BaseAdminViewSet.as_view({'get': 'destroy_all'}), name='bases-destroy'),
    url(r'^api/base/recreate_all/$', BaseAdminViewSet.as_view({'get': 'recreate_all'}), name='bases-recreate'),

    url(r'^api/base/(?P<name>[\w-]+)/start/$', BaseViewSet.as_view({'post': 'start'}), name='base-start'),
    url(r'^api/base/(?P<name>[\w-]+)/stop/$', BaseViewSet.as_view({'post': 'stop'}), name='base-start'),
    url(r'^api/base/(?P<name>[\w-]+)/log/$', BaseLogViewSet.as_view({'get': 'log'}), name='base-log'),
    url(r'^api/base/(?P<name>[\w-]+)/restart/$', BaseViewSet.as_view({'post': 'restart'}), name='base-restart'),
    url(r'^api/base/(?P<name>[\w-]+)/destroy/$', BaseViewSet.as_view({'post': 'destroy'}), name='base-destroy'),
    url(r'^api/base/(?P<name>[\w-]+)/export/$', BaseExportViewSet.as_view({'get': 'export'}), name='base-export'),
    url(r'^api/base/(?P<name>[\w-]+)/transport/$', BaseViewSet.as_view({'post': 'transport'}), name='base-transport'),
    url(r'^api/base/(?P<name>[\w-]+)/apy/$', ApyViewSet.as_view({'get': 'list', 'post': 'create'}), name='apy-list'),
    url(r'^api/public-apy/$', PublicApyViewSet.as_view({'get': 'list'}), name='public-apy-list'),
    url(r'^api/public-apy/(?P<pk>\d+)/$', PublicApyViewSet.as_view({'get': 'retrieve'}), name='public-apy-detail'),
    # Apy CRUD operations
    url(r'^api/base/(?P<name>[\w-]+)/apy/(?P<pk>\d+)/$', ApyViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='apy-detail'),
    url(r'^api/base/(?P<name>[\w-]+)/apy/(?P<pk>\d+)/clone/$', ApyViewSet.as_view({'post': 'clone'}), name='apy-clone'),
    url(r'^api/username/(?P<username>[\w-]+)/base/(?P<name>[\w-]+)/apy/(?P<apy_name>[\w-]+)/execute/$', ApyPublicExecutionViewSet.as_view({'post': 'execute', 'get': 'execute'}), name='apy-public-exec'),
    url(r'^api/base/(?P<name>[\w-]+)/apy/(?P<apy_name>[\w-]+)/execute/$', ApyExecutionViewSet.as_view({'post': 'execute', 'get': 'execute'}), name='apy-exec'),
    url(r'^api/base/(?P<name>[\w-]+)/setting/$', SettingViewSet.as_view({'get': 'list', 'post': 'create'}), name='apy-list'),
    url(r'^api/base/(?P<name>[\w-]+)/setting/(?P<pk>\d+)/$', SettingViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='apy-detail'),
    url(r'^api/base/(?P<name>[\w-]+)/transactions/$', TransactionViewSet.as_view({'get': 'list'}), name='transaction-list'),

    # api-authtoken
    url(r'^api-token-auth/', 'rest_framework.authtoken.views.obtain_auth_token'),

    # home
    url(r'^$', DjendView.as_view(template_name="fastapp/base_list.html"), name="console"),

    # api-docs
    url(r'^api-docs/', include('rest_framework_swagger.urls')),

    # metrics
    #url(r'^metrics/', include('redis_metrics.urls'))
)

from rest_framework.urlpatterns import format_suffix_patterns
urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'api'])
