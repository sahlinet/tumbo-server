import os

import gevent
from django.conf import settings

from core.utils import Connection


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

    def _save(self, filename, content):
        with open(os.path.join(self.root, filename), 'w') as f:
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
