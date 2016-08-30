from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

"""
/login
/logout
/profile

/core/dashboard
/core/admin
/core/api
/core/profile
/userland/USERNAME/project/BASENAME
"""

urlpatterns = patterns('',
    url(r'^$', 'ui.views.home'),
    url(r'^docs/$', 'ui.views.docs'),

    # TODO: not used anymore?
    #url(r'^core/login/$', 'aaa.views.login', name='login'),
    #url(r'^core/logout/$', 'aaa.views.logout', name='core-logout'),
    #url(r'^core/done/$', 'aaa.views.done', name='done'),
    #url(r'^core/profile/$', 'ui.views.profile', name='core-profile'),

    #url(r'^core/admin/', include(admin.site.urls)),
    #url(r'^core/dashboard/', include('core.urls')),
    #url(r'^core/api/', include('core.api_urls')),

    url(r'^userland/', include('core.userland_urls')),
    url(r'^cas/', include('aaa.cas.urls')),
    url(r'^core/', include('core.urls')),
    #url(r'^core/', include('social.apps.django_app.urls', namespace='social'))

)
