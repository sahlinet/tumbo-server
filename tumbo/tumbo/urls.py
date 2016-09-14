from django.conf.urls import patterns, include, url


urlpatterns = patterns('',
    url(r'^$', 'ui.views.home'),
    url(r'^docs/$', 'ui.views.docs'),

    # platform URL's
    url(r'^core/', include('core.urls')),

    # URL's for user projects
    url(r'^userland/', include('core.userland_urls')),

    # CAS login and authentication
    url(r'^cas/', include('aaa.cas.urls')),
)
