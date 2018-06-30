"""Management Command to import a Base from Git.
"""

import logging

from django.core.management.base import BaseCommand

from core.importer import GitImport as git

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

        result = git().import_base(username, name, branch, repo_url)

        logger.info(result)
