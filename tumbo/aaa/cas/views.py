import re
import logging

from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect, render
from django.views.generic import View
from django.views.decorators.cache import never_cache
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.conf import settings

from social.backends.utils import load_backends

from core.utils import create_jwt
from core.models import Base
from aaa.cas.models import Ticket

from django.contrib.auth import get_user_model
User = get_user_model()


logger = logging.getLogger(__name__)

def login(request):
    logging.info("Start login")
    if request.method == "GET":
        service = request.GET['service']
        m = re.match(r".*/userland/(?P<username>.*?)/(?P<basename>.*?)/", service)
        username = m.group('username')
        basename = m.group('basename')
        base = Base.objects.get(name=basename, user__username=username)

        if request.user.is_authenticated:
            user = request.user

        request.session['next'] = service

        return render(request, 'aaa/cas_loginpage.html', {'user': user, 'userland': username, 'basename': basename
                , 'available_backends': load_backends(settings.AUTHENTICATION_BACKENDS)})

    elif request.method == "POST":
        #logger.warn(request)
        username = request.POST['username']
        password = request.POST['password']
        service = request.POST['service']
        user = authenticate(username=username, password=password, redirect_uri="/cas/login/")
        if user is not None:
            if user.is_active:
                auth_login(request, user)
                #return redirect('/core/dashboard/')
                ticket = Ticket.objects.create_ticket(user=user)
                return redirect(service+"?ticket=%s" % ticket.ticket)
            else:
                # Return a 'disabled account' error message
                #...
                return redirect('/disabled')
        else:
            # Return an 'invalid login' error message.
            #...
            return redirect('/')

def verify(request):
    ticket_s = request.GET['ticket']
    service = request.GET['service']

    ticket = Ticket.objects.validate_ticket(ticket_s, service)
    if ticket:
        secret = settings.SECRET_KEY
        token = create_jwt(ticket.user, secret)

        ticket.user.backend = 'django.contrib.auth.backends.ModelBackend'
        #auth_login(request, ticket.user)
    return HttpResponse(token)

def logout(request):
    """Logs out user"""
    auth_logout(request)
    next = request.GET.get("next", "/")
    if "next" in request.session:
        del request.session['next']
    return redirect(next)
