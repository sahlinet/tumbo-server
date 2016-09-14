import logging
import zipfile

from optparse import make_option

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from core.importer import import_base

logger = logging.getLogger("core.executors.remote")

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--username',
            dest='username',
            help='Import base for user'),
        ) + (
        make_option('--file',
            dest='file',
            help='Export file to import'),
        ) + (
        make_option('--name',
            dest='name',
            help='Base name'),
        )

    help = 'Import base'

    def handle(self, *args, **options):

        f = open(options['file'], 'r')
        zf = zipfile.ZipFile(f)

        user = get_user_model().objects.get(username=options['username'])
        override_public = True
        override_private = True

        base = import_base(zf, user, options['name'],
                override_public, override_private)
        base.save()
