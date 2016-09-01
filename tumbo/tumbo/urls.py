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

    url(r'^userland/', include('core.userland_urls')),
    url(r'^cas/', include('aaa.cas.urls')),
    url(r'^core/', include('core.urls')),

)
