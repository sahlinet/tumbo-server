from django.shortcuts import render
from django.shortcuts import redirect

from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import login as auth_login
from django.contrib.auth import authenticate

from ui.decorators import render_to
from ui.views import context


def logout(request):
    """Logs out user"""
    auth_logout(request)
    return redirect('/')


@login_required
@render_to('home.html')
def done(request):
    """Login complete view, displays user data"""
    return context()


def login(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            auth_login(request, user)
            return redirect('/fastapp/')
        else:
            # Return a 'disabled account' error message
            #...
            return redirect('/')
    else:
        # Return an 'invalid login' error message.
        #...
        return redirect('/')
