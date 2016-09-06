from django.conf.urls import patterns, url, include
from django.contrib.auth.decorators import login_required
from aaa.cas.authentication import cas_login
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

from core.api_views import BaseAdminViewSet, BaseViewSet, BaseLogViewSet, SettingViewSet, PublicApyViewSet, ApyViewSet, BaseExportViewSet, BaseImportViewSet, TransportEndpointViewSet, TransactionViewSet, ApyExecutionViewSet

from django.views.decorators.cache import never_cache

# Routers provide an easy way of automatically determining the URL conf
router = routers.DefaultRouter(trailing_slash=True)
router.register(r'apy', ApyViewSet)
router.register(r'base', BaseViewSet)

urlpatterns = patterns('',

    #url(r'(?P<base>[\w-]+)/exec/(?P<id>\d+)/$', \
    #                                        csrf_exempt(login_or_sharedkey(DjendExecView.as_view())), name='exec'),
    url(r'^(?P<username>[\w-]+)/(?P<base>[\w-]+)/static/(?P<name>.+)$', \
                                            cas_login(DjendStaticView.as_view()), name="userland-static"),
    #url(r'^(?P<username>[\w-]+)/api/base/(?P<name>[\w-]+)/apy/(?P<apy_name>[\w-]+)/execute/$', ApyExecutionViewSet.as_view({'post': 'execute', 'get': 'execute'}), name='userland-apy-public-exec'),
    url(r'^(?P<username>[\w-]+)/(?P<name>[\w-]+)/api/apy/(?P<apy_name>[\w-]+)/execute/$', ApyExecutionViewSet.as_view({'post': 'execute', 'get': 'execute'}), name='userland-apy-public-exec'),
    url(r'^(?P<username>[\w-]+)/(?P<base>[\w-]+)/login$', 'aaa.views.loginpage_userland', name='userland-cas-ticketlogin'),
    url(r'^(?P<username>[\w-]+)/(?P<base>[\w-]+)/logout$', 'aaa.views.logout_userland', name='userland-logout'),
    #url(r'^(?P<username>[\w-]+)/(?P<base>[\w-]+)/login$', 'aaa.views.loginpage_userland', name='userland-loginpage'),
    # url(r'^api/base/(?P<name>[\w-]+)/apy/(?P<apy_name>[\w-]+)/execute/$', ApyExecutionViewSet.as_view({'post': 'execute', 'get': 'execute'}), name='userland-apy-exec'),
)
