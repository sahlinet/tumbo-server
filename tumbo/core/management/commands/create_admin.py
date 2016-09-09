import logging

from optparse import make_option

from django.core.management.base import BaseCommand


logger = logging.getLogger("core.executors.remote")


class Command(BaseCommand):
    args = '<poll_id poll_id ...>'
    help = 'Closes the specified poll for voting'

    option_list = BaseCommand.option_list + (
        make_option('--username',
                    action='store',
                    dest='username',
                    default=None,
                    help='Username'),
        make_option('--password',
                    action='store',
                    dest='password',
                    default=None,
                    help='Password'),
        make_option('--email',
                    action='store',
                    dest='email',
                    default=None,
                    help='Email address')
        )

    def handle(self, *args, **options):
        threads = []
        threads_static = []
        
        username = options['username']
        password = options['password']
        email = options['email']

        
        from django.contrib.auth.models import User

        u = User(username=username)
        u.set_password(password)
        u.is_superuser = True
        u.is_staff = True
        u.save()
