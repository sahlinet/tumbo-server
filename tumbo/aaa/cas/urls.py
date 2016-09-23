from django.conf.urls import patterns, url, include

urlpatterns = patterns('',

    url(r'login/$', 'aaa.cas.views.loginpage', name='cas-login'),
    url(r'logout/$', 'aaa.cas.views.logout', name='cas-logout'),
    url(r'verify/$', 'aaa.cas.views.verify', name='cas-ticketverify'),
    url(r'^', include('social.apps.django_app.urls', namespace='social'))
)

