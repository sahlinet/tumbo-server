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
        # repo_url = "git@github.com:sahlinet/tumbo-demoapp.git"
        repo_url = "https://github.com/sahlinet/tumbo-demoapp.git"

        result = git().import_base(username, name, branch, repo_url, repo_ref=True)
        assert result[0] is not None
        assert type(result[1]) is Base

        result = git().import_base(username, name, branch, repo_url, repo_ref=True, repo_path="/tmp/demoapp-test-branch")
        assert result[0] is None
        base_obj = result[1]
        assert type(base_obj) is Base

        old_revision = base_obj.revision

        repo = result[2]
        repo_path = result[3]

        new_file = "{}/asdf_{}.txt".format(repo_path, str(uuid.uuid4()))
        touch = sh.Command("touch")
        touch(new_file)

        repo.git.add(new_file)
        repo.git.commit('-m', 'test commit', author='Philip Sahli <philip@sahli.net>')
        repo.git.push()

        shutil.rmtree(repo_path)

        result = git().import_base(username, name, branch, repo_url, repo_ref=True, repo_path="/tmp/demoapp-test-branch")
        assert result[0] is not None
        base_obj = result[1]
        assert type(base_obj) is Base

        # verify revision changed
        assert old_revision is not base_obj.revision
