from rest_framework import routers

from django.conf.urls import patterns, url

from aaa.cas.authentication import cas_login
from core.views.static import DjendStaticView
from core.api_views import ApyViewSet, ApyExecutionViewSet


# Routers provide an easy way of automatically determining the URL conf
router = routers.DefaultRouter(trailing_slash=True)
router.register(r'apy', ApyViewSet)

urlpatterns = patterns('',

    url(r'^(?P<username>[\w-]+)/(?P<base>[\w-]+)/static/(?P<name>.+)$', \
                                            cas_login(DjendStaticView.as_view()), name="userland-static"),
    url(r'^(?P<username>[\w-]+)/(?P<name>[\w-]+)/api/apy/(?P<apy_name>[\w-]+)/execute/$', ApyExecutionViewSet.as_view({'post': 'execute', 'get': 'execute'}), name='userland-apy-public-exec'),
    url(r'^(?P<username>[\w-]+)/(?P<base>[\w-]+)/login$', 'aaa.views.loginpage_userland', name='userland-cas-ticketlogin'),
    url(r'^(?P<username>[\w-]+)/(?P<base>[\w-]+)/logout/$', 'aaa.views.logout_userland', name='userland-logout'),
)
