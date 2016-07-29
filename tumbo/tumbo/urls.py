from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

"""
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
    url(r'^login/$', 'aaa.views.login', name='login'),
    url(r'^logout/$', 'aaa.views.logout'),
    url(r'^done/$', 'aaa.views.done', name='done'),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^fastapp/', include('core.urls')),

    url(r'^profile/$', 'ui.views.profile'),

    url('', include('social.apps.django_app.urls', namespace='social'))

)
