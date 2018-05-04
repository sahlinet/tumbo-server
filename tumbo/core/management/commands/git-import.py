import datetime
import logging
import shutil
import tempfile
import zipfile

import pytz
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from git import Repo

logger = logging.getLogger("core.management.git-import")


class Command(BaseCommand):
    help = 'Cleanup old transactions and logs'

    # CI=yes python tumbo/manage.py git-import --settings=tumbo.dev

    def handle(self, *args, **options):
        # Check if we have to Repo already

        username = "admin"
        name = "tumbo-demoapp"
        branch = "master"
        repo_url = "git@github.com:sahlinet/tumbo-demoapp.git"

        from core.importer import GitImport as git
        result = git().import_base(username, name, branch, repo_url)

        logger.info(result)


