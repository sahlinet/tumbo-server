"""This management commands create an user in the database with admin privileges."""
import logging
import os

from optparse import make_option

from django.core.management.base import BaseCommand


logger = logging.getLogger("core.executors.remote")


class Command(BaseCommand):
    """Command class."""
    args = '<poll_id poll_id ...>'
    help = 'Updates the superuser'

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

        username = options['username']
        password = options['password']
        print password
        if password.startswith('$'):
            password = os.environ.get(password.replace("$", ""))
        print password

        email = options['email']

        from django.contrib.auth.models import User

        try:
            #u = User(username=username)
            u, created = User.objects.get_or_create(username=username)
            u.set_password(password)
            u.email = email
            u.is_superuser = True
            u.is_staff = True
            u.save()
            if created:
                print "Adminuser '%s' created." % username
            else:
                print "Adminuser '%s' updated." % username
        except Exception, e:
            print e
