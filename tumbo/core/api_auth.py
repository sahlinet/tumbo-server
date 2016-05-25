from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework import exceptions
from django.contrib.auth.models import AnonymousUser


class EveryoneAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        base_name = request.META.get('name', None)
        exec_name = request.META.get('apy_name', None)
        if not exec_name:
            return None

        try:
            base_obj = Base.objects.get(name=exec_name)
            exec_obj = Apy.objects.get(base=base_obj, name=exec_name)
            if not exec_obj.everyone:
                return None
            user =  AnonymousUser()
        except:
            return None
        return (user, None)
