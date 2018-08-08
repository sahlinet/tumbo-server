#!/usr/bin/env python
# -*- coding: utf-8 -*-

import shutil
import urllib
import uuid

import sh
from django.core.urlresolvers import reverse
from rest_framework.test import APIRequestFactory

from core.api_views import WebhookView
from core.importer import GitImport as git
from core.models import Base, StaticFile
from core.tests.tests_all import BaseTestCase


class GitImportTestCase(BaseTestCase):


    def setUp(self):
        super(GitImportTestCase, self).setUp()

        self.username = self.user1.username
        self.name = "tumbo-demoapp"
        self.branch = "test-branch"
        self.repo_url = "https://git:@github.com/sahlinet/tumbo-demoapp.git/"

    def _add_file(self):
        touch = sh.Command("touch")
        mkdir = sh.Command("mkdir")
        echo = sh.Command("echo")
        cp = sh.Command("cp")

        mkdir("-p static".split())

        # Create commit (add file with unicode characters)
        new_file = "{}/static/newfile_{}.txt".format(self.repo_path, str(uuid.uuid4()))
        touch(new_file)
        h = open(new_file, "a")
        echo("öö", _out=h)
        self.repo.git.add(new_file)

        new_file2 = "{}/static/newfile2_{}.txt".format(self.repo_path, str(uuid.uuid4()))
        touch(new_file2)
        self.repo.git.add(new_file2)

        # Add png to test binary file
        png_file = "{}/static/file_{}.png".format(self.repo_path, str(uuid.uuid4()))
        urllib.urlretrieve("https://vignette.wikia.nocookie.net/htmlcss/images/e/e4/PNG_Example_1.png", png_file)
        self.repo.git.add(png_file)

        self.repo.git.config('--global', "user.name", "user name")
        self.repo.git.config('--global', "user.email", "user@domain.com")
        self.repo.git.commit('-m', 'test commit', author='Philip Sahli <philip@sahli.net>')

    def test_git_import_base(self):

        # Initial import
        result = git().import_base(self.username, self.name, self.branch, self.repo_url, repo_ref=True)
        assert result[0] is not None
        assert type(result[1]) is Base

        # Import again, no changes expected
        result = git().import_base(self.username, self.name, self.branch, self.repo_url, repo_ref=True, repo_path="/tmp/demoapp-test-branch")
        assert result[0] is None
        self.base_obj = result[1]
        assert isinstance(self.base_obj, Base)

        # Verify revision on base object
        self.old_revision = self.base_obj.revision

        self.repo = result[2]
        self.repo_path = result[3]


    def test_git_update_base(self, update_only=False):
        if not update_only:
            self.test_git_import_base()

        # Do update
        self._add_file()

        # Import update
        result = git().import_base(self.username, self.name, self.branch, self.repo_url, repo_ref=True, repo_path="/tmp/demoapp-test-branch")
        assert result[0] is not None
        base_obj = result[1]
        assert isinstance(base_obj, Base)

        # Verify revision changed
        assert self.old_revision is not base_obj.revision

    def tearDown(self):
        """Delete checked out repo path.
        """
        try:
            shutil.rmtree("/tmp/demoapp-test-branch")
        except:
            pass


class GitHookTestCase(GitImportTestCase):

    def _call_hook(self, **kwargs):
        hook_url = reverse("base-update-hook", kwargs={'username': self.user1.username, 'name': "tumbo-demoapp"})
        view = WebhookView.as_view({'post': "hook"})
        factory = APIRequestFactory()
        request = factory.post(hook_url, **kwargs)
        response = view(request, **{"username": self.user1.username, "name": "tumbo-demoapp"})
        return response

    def test_git_update_hook_ping(self):
        response = self._call_hook(HTTP_X_GITHUB_EVENT="ping", HTTP_X_FORWARDED_FOR="192.30.252.1")

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'msg': 'pong'})

    def test_git_update_hook_update(self):
        self.test_git_import_base()
        response = self._call_hook(HTTP_X_GITHUB_EVENT="push", HTTP_X_FORWARDED_FOR="192.30.252.1", data={'ref': "refs/heads/test-branch" })

        self.assertEqual(response.status_code, 200)
        assert 'status' in response.content
        assert 'details' in response.content
