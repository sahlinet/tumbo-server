"""Staticfile handling.
"""

import base64
import json
import logging
import os
import sys
from datetime import datetime

import pytz
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache

from core.communication import generate_vhost_configuration
from core.executors.remote import get_static
from core.models import Base, StaticFile
from core.utils import totimestamp

User = get_user_model()

logger = logging.getLogger(__name__)


class NotFound(BaseException):
    pass


class LoadMixin(object):

    def _cache_not_found(self):
        logger.info("cache.get not_found for %s (%s), caching now..." % (
            self.static_name, self.cache_key))
        cache.set(self.cache_key, True,
                  int(settings.TUMBO_STATIC_404_CACHE_SECONDS))

    def _is_cached_not_found(self):
        cached = cache.get(self.cache_key, False)
        if cached:
             logger.info("Cached staticfile '%s' found" % self.cache_key)
        else:
             logger.info("Cached staticfile '%s' not found" % self.cache_key)
        return cached

    def load(self):
        """
        Implements the logic for loading files from storages. If previously a not_found was cached, raise NotFound Exception.
        Otherwise call _load of the storage implementation. _load is called for every storage, thus not_found is cached only for this particular implementation.
        """
        r = None

        try:
            logger.debug("_load in %s" % self.__class__.__name__)
            if self._is_cached_not_found():
                logger.debug("cached not_found exists, not loading again in the next %s seconds" %
                             settings.TUMBO_STATIC_CACHE_SECONDS)
                r = None
            else:
                r = self._load()
        except NotFound, e:
            self._cache_not_found()
        except Exception, e:
            logger.error(e)
            raise e

        logger.debug("Returned: %s" % r)
        return r


class StaticfileFactory(LoadMixin):

    def __init__(self, *args, **kwargs):
        username = args[0]
        project_name = args[1]
        static_name = args[2]
        self.static_path = "%s/%s/%s" % (project_name, "static", static_name)
        logger.debug("Staticfile %s" % self.static_path)

        self.project_name = project_name
        self.static_name = static_name
        self.username = username

        self.now = datetime.now()

        self.base_obj = Base.objects.get(
            user__username=username, name=project_name)

        self.cache_key = "%s-%s-%s" % (self.base_obj.user.username,
                                       self.base_obj.name, self.static_path)
        self.cache_obj = cache.get(self.cache_key, None)

    def lookup(self):
        file = None

        if self.cache_obj:
            logger.debug("Return cached version of %s" % self.static_path)
            file = self.cache_obj.get('f', None)
            last_modified = self.cache_obj.get('lm', None)
            return StorageStaticFile(username=self.username,
                                     project=self.project_name,
                                     name=self.static_name,
                                     content=file,
                                     last_modified=last_modified,
                                     storage=self.__class__.__name__,
                                     cached=True)

        else:
            logger.debug("%s: not in cache" % self.static_path)

            storages = [
                # DevRepoStaticfile,
                DBStaticfile,
                WorkerModuleStaticfile
            ]
            file_obj = None
            for storage in storages:
                file_obj = storage(
                    self.username, self.project_name, self.static_name).load()
                if file_obj:
                    logger.info("Staticfile %s found in storage %s" %
                                (file_obj, storage.__name__))
                    break

            if file_obj is not None:
                if 'content="no-cache"' in file_obj.content:
                    logger.debug(
                        "Not caching because no-cache present in HTML")
                else:
                    logger.info("Caching %s (%s)" %
                                 (self.cache_key, file_obj.last_modified))
                    cache.set(self.cache_key, {
                        'f': file_obj.content,
                        'lm': totimestamp(file_obj.last_modified)
                    }, int(settings.TUMBO_STATIC_CACHE_SECONDS))
                return file_obj
            raise NotFound(self.static_name)


class StorageStaticFile(object):
    """
    file = StorageStaticFile(username=self.username,
                      project=self.project,
                      name=self.static_name,
                      content=self.content,
                      last_modified=self.last_modified,
                      storage=self.__class__.__name__,
                      cached=True)
    """

    def __init__(self, *args, **kwargs):
        self.username = kwargs['username']
        self.project = kwargs['project']
        self.name = kwargs['name']

        self.content = kwargs['content']

        self.last_modified = kwargs['last_modified']
        self.storage = kwargs['storage']

        self.cached = kwargs.get('cached', False)
        self.from_cache = kwargs.get('from_cache', False)

        logger.info("StorageStaticFile '%s'" % self)

    def __str__(self):
        return "%s:%s:%s" % (self.username, self.project, self.name)


class DevRepoStaticfile(StaticfileFactory):

    def _load(self):

        REPOSITORIES_PATH = getattr(settings, "TUMBO_REPOSITORIES_PATH", None)
        if "runserver" in sys.argv and REPOSITORIES_PATH:
            # for debugging with local runserver not loading from repository
            # but from local filesystem
            try:
                filepath = os.path.join(REPOSITORIES_PATH, self.static_path)
                file = open(filepath, 'r').read()
                size = os.path.getsize(filepath)
                logger.debug("%s: load from local filesystem (repositories) (%s) (%s)" % (
                    self.static_path, filepath, size))
                last_modified = datetime.fromtimestamp(
                    os.stat(filepath).st_mtime)
                #obj, created = StaticFile.objects.get_or_create(base=self.base_obj, name=self.static_path, storage="FS")

                try:
                    obj, created = StaticFile.objects.get_or_create(
                        base=self.base_obj, name=self.static_path, storage="FS")
                except Exception:
                    StaticFile.objects.filter(
                        base=self.base_obj, name=self.static_path, storage="FS").delete()
                    obj, created = StaticFile.objects.get_or_create(
                        base=self.base_obj, name=self.static_path, storage="FS")
                logger.info("StaticFile Obj: " + str(obj) + " " + str(created))
                if created or obj.rev != os.stat(filepath).st_mtime:
                    obj.rev = os.stat(filepath).st_mtime
                    obj.accessed = self.now
                    obj.save()
                file_obj = StorageStaticFile(username=self.username,
                                             project=self.project_name,
                                             name=self.static_name,
                                             content=file,
                                             last_modified=last_modified,
                                             storage=self.__class__.__name__,
                                             cached=True)
                return file_obj

            except IOError, e:
                logger.error(e)
                raise NotFound()


class DBStaticfile(StaticfileFactory):

    def _load(self):
        try:
            obj = StaticFile.objects.get(
                base=self.base_obj, name=self.static_path, storage="DB")

            logger.debug("%s: load from database" %
                         self.static_path)
            last_modified = obj.updated

            obj.accessed = self.now
            obj.save()

            obj.last_modified = last_modified.replace(tzinfo=pytz.UTC)
            # buffer to string conversion
            obj.content = "%s" % obj.content

            return obj

        except IOError, e:
            logger.warn(e)
            raise NotFound()


class WorkerModuleStaticfile(StaticfileFactory):

    def _load(self):
        try:
            if not self.base_obj.state:
                raise Exception("Skipping because worker is not running")
            # try to load from installed module in worker
            logger.debug("%s: load from module in worker" % self.static_path)
            response_data = get_static(
                json.dumps({"base_name": self.base_obj.name,
                            "path": self.static_path}),
                generate_vhost_configuration(
                    self.base_obj.user.username,
                    self.base_obj.name
                ),
                self.base_obj.name,
                self.base_obj.executor.password
            )
            data = json.loads(response_data)

            if data['status'] == "ERROR":
                logger.error("%s: ERROR response from worker" %
                             self.static_path)
                raise Exception(response_data)
            elif data['status'] == "TIMEOUT":
                logger.error("%s: TIMEOT response from worker" %
                             self.static_path)
                raise Exception("Timeout")
            elif data['status'] == "OK":
                file = base64.b64decode(data['file'])
                last_modified = datetime.fromtimestamp(data['LM'])
                logger.debug("%s: file received from worker with timestamp: %s" % (
                    self.static_path, str(last_modified)))

                obj, created = StaticFile.objects.get_or_create(
                    base=self.base_obj, name=self.static_path, storage="MO")
                if obj.rev != data['LM'] or created:
                    obj.rev = data['LM']
                    obj.accessed = self.now
                    obj.save()

                file_obj = StorageStaticFile(username=self.username,
                                             project=self.project_name,
                                             name=self.static_name,
                                             content=file,
                                             last_modified=last_modified,
                                             storage=self.__class__.__name__,
                                             cached=True)
                return file_obj

        except Exception, e:
            logger.error(e)
            raise NotFound()
