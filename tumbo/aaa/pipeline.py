from django.conf import settings
from django.http import HttpResponse
from django.http.shortcuts import redirect


def _is_member(user, group):
    print user, group
    print user.groups.filter(name=group).exists()
    return user.groups.filter(name=group).exists()


def restrict_user(backend, username, response, *args):
    if username.is_superuser:
        return

    #group = getattr(settings, "SOCIAL_AUTH_USER_GROUP", None)
    # if group:
    #    if not _is_member(user, group):
    #        return HttpResponse("Login forbidden.")


# def redirect_with_ticket_to_service(backend, user, response, *args, **kwargs):
#     print backend, user, response, args, str(kwargs)
#    response = redirect(service + "?ticket=aaa")
