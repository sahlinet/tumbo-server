"""Module for Storage classes.
"""

import logging
import os

import gevent
from django.conf import settings

from core.models import StaticFile

logger = logging.getLogger(__name__)

class Storage(object):
    """Factory class to create Storage class.

    Storage in this context is used to write data changed in UI to the storage.
    """

    @staticmethod
    def factory(type=None):
        """class method to return class with implementation.

        Returns:
            [BaseStorage Subclass] -- Concret class.
        """

        if type:
            return DBStorage
        if hasattr(settings, "TUMBO_REPOSITORIES_PATH"):
            return LocalStorage
        assert 0, "bad storage class creation: " + str(type)


class BaseStorage(object):
    """Base Storage class to override.
    """

    def __init__(self, instance):
        """initalize with an instance.

        Arguments:
            instance {Model object} -- Any of Apy, Base or Setting
        """

        self.instance = instance
        if "Base" in type(self.instance).__name__:
            self.base = self.instance
            self.username = self.instance.user.username
            self.base_name = self.instance.name
            self.config = self.instance.config
        else:
            self.base = self.instance.base
            self.username = self.instance.base.user.username
            self.instance_name = self.instance.base.name
            self.base_name = self.instance.base.name
            self.config = self.instance.base.config


class LocalStorage(BaseStorage):
    """Class for Local Storage.
    """

    def __init__(self, instance):
        super(LocalStorage, self).__init__(instance)

        self.root = os.path.join(settings.TUMBO_REPOSITORIES_PATH)

        path = os.path.join(self.root, self.base_name)
        static_path = os.path.join(*[self.root, self.base_name, "static"])
        for p in [path, static_path]:
            if not os.path.exists(p):
                os.makedirs(p)

    def _save(self, filename, content):
        if not os.path.exists(os.path.join(self.root, os.path.dirname(filename))):
            os.makedirs(os.path.join(self.root, os.path.dirname(filename)))

        with open(os.path.join(self.root, filename), 'w+') as f:
            f.write(content)
            f.close()

    def _save_config(self):
        self._save("%s/%s/app.config" %
                   (self.root, self.base_name), self.config)

    def delete(self, filename):
        os.remove(os.path.join(self.root, filename))
        self._save_config()

    def put(self, filename, content):
        self._save(filename, content)
        self._save_config()

    def create_folder(self):
        if not os.path.exists(self.root):
            os.makedirs(self.root)
        self._save_config()

    def directory_zip(self, path, zf):
        logger.info("Adding recursive %s to zip" % os.path.join(self.root, path))
        for root, _, files in os.walk(os.path.join(self.root, path)):
            #for folder in subFolders:
                print root
                for sfile in files:
                    filePath = root + "/" + sfile
                    print "filePath: " + filePath
                    f = open(filePath, 'r')
                    filePath_zip = filePath.replace(self.root + "/" + self.base_name + "/", "")
                    logger.info("Add file '%s' as '%s' to zip" % (filePath, filePath_zip))
                    zf.writestr(filePath_zip, f.read())
                    f.close()
        return zf

class DBStorage(BaseStorage):
    """Class for Dropbox Storage.
    """

    def __init__(self, instance):
        super(DBStorage, self).__init__(instance)

    def delete(self, filename):
        staticfile_obj = StaticFile.objects.get(
                base=self.instance,
                name=filename,
                storage="DB"
        )
        staticfile_obj.delete()

    def rename(self, filename_from, filename_to):
        staticfile_obj = StaticFile.objects.get(
                base = self.instance,
                name = filename_from,
                storage = "DB"
        )
        staticfile_obj.filename = filename_to
        staticfile_obj.save()

    def put(self, filename, content):
        staticfile_obj, created = StaticFile.objects.get_or_create(
                base = self.instance,
                name = filename,
                storage = "DB"
        )
        if not created:
            # TODO: remove from cache
            pass

        staticfile_obj.content = content
        staticfile_obj.save()