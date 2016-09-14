from django.shortcuts import redirect
from django.contrib.auth import logout as auth_logout

from ui.decorators import render_to

from django.conf import settings

from tumbo import __VERSION__ as TUMBO_VERSION

from rest_framework.authtoken.models import Token
from social.backends.utils import load_backends
from core.models import AuthProfile


def context(**extra):
    return dict({
        # 'plus_id': getattr(settings, 'SOCIAL_AUTH_GOOGLE_PLUS_KEY', None),
        # 'plus_scope': ' '.join(GooglePlusAuth.DEFAULT_SCOPE),
        'available_backends': load_backends(settings.AUTHENTICATION_BACKENDS),
        'PLANET_VERSION': TUMBO_VERSION,
        'TUMBO_STATIC_CACHE_SECONDS': settings.TUMBO_STATIC_CACHE_SECONDS
    }, **extra)


HOME_TEMPLATE = getattr(settings, 'HOME_TEMPLATE', 'home.html')
PROFILE_TEMPLATE = getattr(settings, 'PROFILE_TEMPLATE', 'profile.html')


@render_to(HOME_TEMPLATE)
def home(request):
    """Home view, displays login mechanism"""
    # if request.user.is_authenticated():
    #    return redirect('/fastapp')
    return context()


@render_to(PROFILE_TEMPLATE)
def profile(request):
    """Home view, displays login mechanism"""
    auth, created = AuthProfile.objects.get_or_create(user=request.user)
    if not request.user.is_authenticated():
        raise Exception("Not Logged in")

    token, created = Token.objects.get_or_create(user=request.user)
    context = {}
    context['TOKEN'] = token.key

    return context


def logout(request):
    """Logs out user"""
    auth_logout(request)
    return redirect('/')


@render_to("documentation.html")
def docs(request):
    """Home view, displays login mechanism"""
    # if request.user.is_authenticated():
    #    return redirect('/fastapp')
    return context()
