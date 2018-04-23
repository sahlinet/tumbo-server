import os
import sys

import gevent
from django.conf import settings

import logging 
from core.utils import Connection

logger = logging.getLogger(__name__)

class Storage(object):
    """Factory class to create Storage class.

    Storage in this context is used to write data changed in UI to the storage.
    """

    def factory():
        """class method to return class with implementation.

        Returns:
            [BaseStorage Subclass] -- Concret class.
        """

        if hasattr(settings, "TUMBO_REPOSITORIES_PATH"):
            return LocalStorage
        assert 0, "bad storage class creation: " + type
    factory = staticmethod(factory)


class BaseStorage(object):
    """Base Storage class to override.
    """

    def __init__(self, instance):
        """initalize with an instance.

        Arguments:
            instance {Model object} -- Any of Apy, Base or Setting
        """

        self.instance = instance
        #if isinstance(self.instance, Base):
        if "Base" in type(self.instance).__name__:
            print self

            self.username = self.instance.user.username
            self.base_name = self.instance.name
            self.config = self.instance.config
        else:
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
        print os.path.exists(os.path.dirname(filename))
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
                for file in files:
                    filePath = root + "/" + file
                    print "filePath: " + filePath
                    f = open(filePath, 'r')
                    filePath_zip = filePath.replace(self.root + "/" + self.base_name + "/", "")
                    #print filePath_zip
                    logger.info("Add file '%s' as '%s' to zip" % (filePath, filePath_zip))
                    zf.writestr(filePath_zip, f.read())
                    f.close()
        return zf


class DropboxStorage(BaseStorage):
    """Class for Dropbox Storage.
    """

    def __init__(self, instance):
        super(DropboxStorage, self).__init__(instance)

        self.connection = Connection(
            instance.base.user.authprofile.dropbox_access_token)

    def _save_config(self):
        gevent.spawn(self.connection.put_file("%s/%s/app.config" %
                                              (self.username, self.base_name), self.config))

    def delete(self, filename):
        gevent.spawn(self.connection.delete_file(filename %
                                                 (self.base_name, self.instance_name)))
        self._save_config()

    def put(self, filename, content):
        result = self.connection.put_file(filename % (
            self.base_name, self.instance_name), content)
        self._save_config()
        return result

    def create_folder(self, filename):
        self.connection.create_folder(
            "%s/%s" % (self.username, self.instance_name))
        self._save_config()

    def directory_zip(self, path, zf):
        self.connection.directory_zip(self.username + "/" + path, zf)
        return zf
