import logging
import os
import json
import base64

from django.template import TemplateDoesNotExist
from django.template.loader import BaseLoader
from core.utils import Connection

from django.conf import settings

from core.models import Base
from core.executors.remote import get_static
from core.queue import generate_vhost_configuration

logger = logging.getLogger(__name__)



class FastappBaseLoader(BaseLoader):
    is_usable = True
    
    def get_file(self, template_name, short_name, base_model):
        raise NotImplementedError("get_file method is missing on " % self.__class__.name)

    def load_template_source(self, template_name, template_dirs=None):
        logger.debug("Trying to load template %s" % str(template_name.split(":")))
        if ":" in template_name:
            username, base, short_name = template_name.split(":")
            try:
                base_model = Base.objects.get(name=base)
                f, template_name = self.get_file(template_name, short_name, base_model)
                return f, template_name
            except Exception, e:
                pass
        raise TemplateDoesNotExist()
        

    load_template_source.is_usable = True
"""
Wrapper for loading templates from the filesystem.
"""

class RemoteWorkerLoader(FastappBaseLoader):

  def get_file(self, template_name, short_name, base_model):
        logger.debug("%s: load from module in worker" % template_name)
        response_data = get_static(
            json.dumps({"base_name": base_model.name, "path": short_name}),
            generate_vhost_configuration(
                base_model.user.username,
                base_model.name
                ),
            base_model.name,
            base_model.executor.password
            )
        data = json.loads(response_data)
        if data['status'] == "ERROR":
            logger.error("%s: ERROR response from worker" % template_name)
            raise TemplateDoesNotExist()
        elif data['status'] == "TIMEOUT":
            raise TemplateDoesNotExist()
        elif data['status'] == "OK":
            file = base64.b64decode(data['file'])
            logger.info("%s: file received from worker" % template_name)
        elif data['status'] == "NOT_FOUND":
            raise TemplateDoesNotExist()
        return file, template_name


class DropboxAppFolderLoader(FastappBaseLoader):

  def get_file(self, template_name, short_name, base_model):
        connection = Connection(base_model.user.authprofile.access_token)
        logging.info("get_file_content %s" % template_name)
        f = connection.get_file_content(base+"/"+template_name)
        logging.info("get_file_content %s done" % template_name)
        data = json.loads(response_data)

        return f, template_name


class DevLocalRepositoryPathLoader(FastappBaseLoader):

  def get_file(self, template_name, short_name, base_model):
        REPOSITORIES_PATH = getattr(settings, "TUMBO_REPOSITORIES_PATH", None)
        if REPOSITORIES_PATH:
            logger.debug("in DevLocalRepositoryPathLoader")
            try:
                filepath = os.path.join(REPOSITORIES_PATH, os.path.join(base_model.name, short_name))
                file = open(filepath, 'r')
                #size = os.path.getsize(filepath)
                logger.debug("%s: load from local filesystem (repositories) (%s)" % (template_name, filepath))
                #last_modified = datetime.fromtimestamp(os.stat(filepath).st_mtime)
            except Exception, e:
                raise TemplateDoesNotExist()
            return file.read(), template_name
        raise TemplateDoesNotExist()
