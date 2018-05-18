import shutil
import uuid

import sh

from core.importer import GitImport as git
from core.models import Base
from core.tests.tests_all import BaseTestCase


class GitImportTestCase(BaseTestCase):

    def test_git_import_base(self):

        username = self.user1.username
        name = "tumbo-demoapp"
        branch = "test-branch"
        repo_url = "https://git:@github.com/sahlinet/tumbo-demoapp.git/"

        # Initial import
        result = git().import_base(username, name, branch, repo_url, repo_ref=True)
        assert result[0] is not None
        assert type(result[1]) is Base

        # Import again, no changes expected
        result = git().import_base(username, name, branch, repo_url, repo_ref=True, repo_path="/tmp/demoapp-test-branch")
        assert result[0] is None
        base_obj = result[1]
        assert isinstance(base_obj, Base)

        # Verify revision on base object
        old_revision = base_obj.revision

        repo = result[2]
        repo_path = result[3]

        # Create commit (add file)
        new_file = "{}/asdf_{}.txt".format(repo_path, str(uuid.uuid4()))
        touch = sh.Command("touch")
        touch(new_file)

        repo.git.add(new_file)
        repo.git.config('--global', "user.name", "user name")
        repo.git.config('--global', "user.email", "user@domain.com")
        repo.git.commit('-m', 'test commit', author='Philip Sahli <philip@sahli.net>')
        # repo.git.push()

        # Import update
        result = git().import_base(username, name, branch, repo_url, repo_ref=True, repo_path="/tmp/demoapp-test-branch")
        assert result[0] is not None
        base_obj = result[1]
        assert isinstance(base_obj, Base)

        # Verify revision changed
        assert old_revision is not base_obj.revision

    def tearDown(self):
        """Delete checked out repo path.
        """
        shutil.rmtree("/tmp/demoapp-test-branch")