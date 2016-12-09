from rest_framework import routers

from django.views.decorators.cache import never_cache
from django.conf.urls import patterns, url, include
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import admin

from core.views import DjendBaseView, DjendBaseDeleteView, \
        DjendBaseSaveView, \
        DjendBaseCreateView, \
        DjendExecDeleteView, \
        DjendExecView, \
        login_or_sharedkey, dropbox_auth_finish, dropbox_auth_start, dropbox_auth_disconnect, DjendView, \
        DjendBaseRenameView, CockpitView, DropboxNotifyView, \
        change_password
from core.views.static import DjendStaticView

from core.api_views import BaseViewSet, ApyViewSet


# Routers provide an easy way of automatically determining the URL conf
router = routers.DefaultRouter(trailing_slash=True)
router.register(r'apy', ApyViewSet)
router.register(r'base', BaseViewSet)

urlpatterns = patterns('',

    # used for login scope -> SESSION_COOKIE_PATH
    url(r'^$', 'aaa.views.dummy', name='root'),

    url(r'login/$', 'aaa.views.login', name='login'),
    url(r'logout/$', 'aaa.views.logout', name='core-logout'),
    url(r'done/$', 'aaa.views.done', name='done'),
    url(r'profile/$', 'ui.views.profile', name='core-profile'),

    url(r'admin/', include(admin.site.urls)),
    #url(r'dashboard/', include('core.urls')),
    url(r'api/', include('core.api_urls')),

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

    # static (userland)
    url(r'(?P<base>[\w-]+)/static/(?P<name>.+)$', \
                                            login_or_sharedkey(DjendStaticView.as_view())),

    # home
    url(r'^dashboard/$', DjendView.as_view(template_name="fastapp/base_list.html"), name="console"),
)
