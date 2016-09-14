from django.http import HttpResponse
from django.conf import settings

def _is_member(user):
    return user.groups.filter(name='users').exists()

def restrict_user(backend, user, response, *args, **kwargs):
    if hasattr(settings, "RESTRICTED_TO_USERS"):
        if _is_member(user):
            return HttpResponse("Not allowed to login")

def redirect_with_ticket_to_service(backend, user, response, *args, **kwargs):
    response = redirect(service+"?ticket=aaa")
