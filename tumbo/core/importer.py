import os
import logging
import shutil
import tempfile
import zipfile
from distutils.util import strtobool

from configobj import ConfigObj
from django.contrib.auth.models import User
from django.db import transaction
from git import Repo

# from core.models import Storage
from core.models import Apy, Base, Setting
from core.storage import Storage

logger = logging.getLogger(__name__)


def _read_config(app_config):
    appconfig = ConfigObj(app_config)
    return appconfig


def _handle_settings(settings, base_obj, override_public=False, override_private=False):
    """
    dict with settings (k, v)
    """
    # get settings
    for k, v in settings.items():
        setting_obj, _ = Setting.objects.get_or_create(
            base=base_obj, key=k)
        # set if empty
        if not setting_obj.value:
            setting_obj.value = v['value']
        # override_public
        if setting_obj.public and override_public:
            setting_obj.value = v['value']
        # override_private
        if not setting_obj.public and override_private:
            setting_obj.value = v['value']
        setting_obj.public = strtobool(v['public'])
        setting_obj.save()


def _handle_apy(filename, content, base_obj, appconfig):
    name = filename.replace(".py", "")
    apy, _ = Apy.objects.get_or_create(base=base_obj, name=name)
    apy.module = content
    description = appconfig['modules'][name]['description']
    if description:
        apy.description = description
    schedule = hasattr(appconfig['modules'][name], "schedule")
    if schedule:
        apy.schedule = appconfig['modules'][name]['schedule']
    else:
        apy.schedule = ""
    public = appconfig['modules'][name].get('public', None)
    if public:
        apy.public = strtobool(public)
    apy.save()


def import_base(zf, user_obj, name, override_public, override_private, source_type="zip", source=None, revision=None):
    base, created = Base.objects.get_or_create(user=user_obj, name=name)
    if revision:
        base.revision = revision
        base.source = source
        base.source_type = "GIT"

    if not created:
        logger.info("base '%s' did already exist" % name)
    base.save()

    Storage.factory(base)
    # app.config
    appconfig = _read_config(zf.open("app.config"))

    # Apy
    for apy in appconfig['modules'].keys():
        filename = appconfig['modules'][apy]['module']
        apy_content = zf.open(filename).read()
        _handle_apy(filename, apy_content, base, appconfig)
        logger.info("apy: filename=%s" % filename)

    # Access
    access = appconfig.get('access', None)
    if access:
        base.static_public = strtobool(access['static_public'])
        base.public = strtobool(access['public'])

        logger.info("access: static_public=%s, public=%s" %
                    (base.static_public, base.public))

    # Settings
    settings = appconfig['settings']
    _handle_settings(settings, base)

    filelist = zf.namelist()
    for filename in filelist:
        # ignore files starting with '__'
        if filename.startswith('__') or not filename.startswith('static'):
            continue

        # static
        logger.info("staticfile: "+filename)
        content = zf.open(filename).read()
        if filename == "index.html":
            base.content = content
            base.save()

        if "static" in filename and not filename.endswith("/"):
            _handle_static(source_type, base, filename, content)

    return base


def _delete_static(source_type, base, filename):
    filename = base.name + "/" + filename
    if source_type == "GIT":
        storage = Storage.factory(base, type="DB")
        storage.delete(filename)
    else:
        storage.delete(filename)


def _handle_static(source_type, base, filename, content):
    if source_type == "GIT":
        storage = Storage.factory(base, type="DB")
        filename = base.name + "/" + filename
        storage.put(filename, content)
    else:
        sfile = "%s/%s" % (base.name, filename)
        storage.put(sfile, content)


source_type = "GIT"

class GitImport(object):

    def import_base(self, username, name, branch, repo_url, repo_ref=False, repo_path=None):
        user_obj = User.objects.get(username=username)
        num_results = Base.objects.filter(user=user_obj, name=name).count()
        initial = False
        if num_results == 0:
            initial = True
        else:
            try:
                base_obj = Base.objects.get(
                    user=user_obj, name=name, source_type=source_type)
                revision = base_obj.revision

                if not base_obj.revision:
                    initial = True
            except Base.DoesNotExist:
                raise Exception("Base already exists but not as Git project.")

        try:
            with transaction.atomic():

                if not repo_path:
                    repo_path = tempfile.mkdtemp()
                    repo = Repo.clone_from(repo_url, repo_path)
                else:
                    if not os.path.exists(repo_path):
                        repo = Repo.clone_from(repo_url, repo_path)
                    else:
                        repo = Repo(repo_path)
                if branch:
                    repo.git.checkout(branch)

                sha = repo.head.object.hexsha
                short_sha = repo.git.rev_parse(sha, short=4)

                if initial:
                    # Initial import

                    # create zip ball
                    with open('/tmp/clone.zip', 'wb') as archive_file:
                        repo.archive(archive_file, format='zip')
                        # import all
                    with open('/tmp/clone.zip', 'r') as archive_file:
                        zf = zipfile.ZipFile(archive_file)
                        base_obj = import_base(zf, user_obj, name, override_public=False,
                                    override_private=False, source_type=source_type, source=repo_url, revision=short_sha)
                        return short_sha, base_obj
                else:
                    if short_sha == revision:
                        print "Nothing changed"
                        r = None, base_obj
                    else:
                        commit_old = repo.commit(revision)
                        commit_new = repo.commit(short_sha)
                        diff_index = commit_old.diff(commit_new)

                        logger.info("Commit message: %s" % commit_new.message)
                        logger.info("Diffing %s...%s" % (revision, short_sha))

                        # added file detected
                        for change_type in ['A', 'M', 'D', 'R']:
                            for diff_item in diff_index.iter_change_type(change_type):

                                # Rename
                                if diff_item.change_type == "R":
                                    # rename in database
                                    logger.info("* file renamed from %s to %s" % (
                                        diff_item.rename_from, diff_item.rename_to))

                                # Add
                                elif diff_item.change_type == "A" or diff_item.change_type == "R100" or diff_item.change_type == "M":
                                    # Use R100 if a previously deleted file is added again.
                                    print "* file %s was added / modified" % diff_item.a_path
                                    new, _ = self.blobs(diff_item)

                                    filename = diff_item.a_path
                                    content = new

                                    if "static" in filename:
                                        filename = base_obj.name + "/" + filename
                                        _handle_static(
                                            source_type, base_obj, filename, content)
                                        logger.info(
                                            "* file %s saved" % filename)

                                # # Modified
                                # elif diff_item.change_type == "M":
                                #     print "* file %s was modified" % diff_item.a_path
                                #     new, _ = self.blobs(diff_item)

                                # Delete
                                elif diff_item.change_type == "D":
                                    logger.info("* file %s was deleted" %
                                                diff_item.a_path)

                                    if "static" in filename:
                                        _delete_static(
                                            source_type, base_obj, filename)
                                else:
                                    raise Exception(
                                        "change_type '%s' unknown." % diff_item.change_type)

                        base_obj.revision = short_sha

                        base_obj.save()

                        r = short_sha, base_obj
        except Exception, e:
            # import traceback
            # traceback.print_exc()
            # print dir(e)
            # print e.__dict__
            if hasattr(e, "stderr"):
                raise Exception(e.stderr)
            raise e
        finally:
            if not repo_ref:
                shutil.rmtree(repo_path)
        if repo_ref:
            return r + (repo, repo_path,)
        return r

    def blobs(self, diff_item):
        # if diff_item.b_blob:
        #     print("B blob (new):\n{}".format(
        #         diff_item.b_blob.data_stream.read().decode('utf-8')))
        # if diff_item.a_blob:
        #     print("A blob (old):\n{}".format(
        #         diff_item.a_blob.data_stream.read().decode('utf-8')))
        new = diff_item.b_blob.data_stream.read().decode(
            'utf-8') if diff_item.b_blob else None
        old = diff_item.a_blob.data_stream.read().decode(
            'utf-8') if diff_item.a_blob else None
        return new, old
