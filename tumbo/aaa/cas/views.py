
import re
import logging

from urlparse import urlparse

from social.backends.utils import load_backends

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.conf import settings

from core.utils import create_jwt
from core.models import Base
from aaa.cas.models import Ticket

User = get_user_model()


logger = logging.getLogger(__name__)

def loginpage(request):
    """
    If a user wants to login, he opens the url named `cas-login`, which renders the cas_loginpage.html.
    """

    logging.info("Start login for accessing a base")
    if request.method == "GET":
        service = request.GET['service']
        m = re.match(r".*/userland/(?P<username>.*?)/(?P<basename>.*?)/", service)
        if m:
            # we received an URI
            username = m.group('username')
            basename = m.group('basename')
            Base.objects.get(name=basename, user__username=username)
            request.session['next'] = service
        else:
            # we received an host, project is proxed
            host = urlparse(service).netloc
            base = Base.objects.get(frontend_host=host)
            username = base.user.username
            basename = base.name
            request.session['next'] = "https://%s" % host

        if request.user.is_authenticated:
            user = request.user

        logger.info("Next: "+request.session['next'])

        return render(request, 'aaa/cas_loginpage.html', {'user': user, 'userland': username, 'basename': basename
                , 'available_backends': load_backends(settings.AUTHENTICATION_BACKENDS)})

    elif request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        service = request.POST['service']
        user = authenticate(username=username, password=password, redirect_uri="/cas/login/")
        if user is not None:
            if user.is_active:
                auth_login(request, user)
                ticket = Ticket.objects.create_ticket(user=user)
                return redirect(service+"?ticket=%s" % ticket.ticket)
            else:
                return redirect('/disabled')
        else:
            # Return an 'invalid login' error message.
            #...
            return redirect('/')


def verify(request):
    """
    Used for verifying a ticket, if successfull it returns a JWT for the user object.
    """
    ticket_s = request.GET['ticket']
    service = request.GET['service']

    ticket = Ticket.objects.validate_ticket(ticket_s, service)
    if ticket:
        secret = settings.SECRET_KEY
        token = create_jwt(ticket.user, secret)

        ticket.user.backend = 'django.contrib.auth.backends.ModelBackend'
    return HttpResponse(token)

def logout(request):
    """Logs out user"""
    auth_logout(request)
    next = request.GET.get("next", "/")
    if "next" in request.session:
        del request.session['next']
    return redirect(next)
