import logging

from django.shortcuts import render
from django.shortcuts import redirect

from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import login as auth_login
from django.contrib.auth import authenticate
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.core.urlresolvers import reverse

from social.backends.utils import load_backends

from core.models import Base
from ui.views import context

from ui.decorators import render_to
from ui.views import context

logger = logging.getLogger(__name__)

def dummy(request):
    raise Exception("Dummy")

def logout(request):
    """Logs out user"""
    auth_logout(request)
    return redirect('/')

def logout_userland(request, username, base):
    """Logs out user"""
    logger.info("logout_userland for %s/%s" % (username, base))
    auth_logout(request)
    return redirect(reverse("cas-logout")+"?next="+request.GET.get("next", None))


@login_required
@render_to('home.html')
def done(request):
    """Login complete view, displays user data"""
    return context()

def loginpage_userland(request, username, base):
    base = get_object_or_404(Base, name=base)
    return render(request, 'aaa/cas_loginpage.html', {'userland': username, 'base': base.name
                , 'available_backends': load_backends(settings.AUTHENTICATION_BACKENDS)})

def login(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            auth_login(request, user)
            return redirect('/core/dashboard/')
        else:
            # Return a 'disabled account' error message
            return redirect('/')
    else:
        # Return an 'invalid login' error message.
        return redirect('/')
