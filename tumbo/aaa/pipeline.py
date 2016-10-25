from django.http import HttpResponse
from django.conf import settings

def _is_member(user, group):
    print user.groups.filter(name=group).exists()
    return user.groups.filter(name=group).exists()

def restrict_user(backend, user, response, *args, **kwargs):
    if user.is_superuser: return

    group = getattr(settings, "SOCIAL_AUTH_USER_GROUP", None)
    if group:
        if not _is_member(user, group):
            return HttpResponse("Login forbidden.")

def redirect_with_ticket_to_service(backend, user, response, *args, **kwargs):
    response = redirect(service+"?ticket=aaa")
