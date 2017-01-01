import logging
import os
import json
import base64

from django.template import TemplateDoesNotExist
from django.template.loaders.base import Loader
from core.utils import Connection

from django.conf import settings

from core.models import Base
from core.executors.remote import get_static
from core.queue import generate_vhost_configuration
from core.staticfiles import NotFound, StaticfileFactory

logger = logging.getLogger(__name__)


class FastappLoader(Loader):
    is_usable = True

    def get_file(self, template_name, short_name, base_model):
        username, project, name = template_name.split(":")
        if name.startswith("static/"):
            name = name.replace("static/", "")

        try:
            file_fact = StaticfileFactory(username, project, name)
            file_obj = file_fact.lookup()
            file = file_obj.content
            return file, template_name
        except NotFound, e:
            raise TemplateDoesNotExist(name)
        except Exception, e:
            raise e

    def load_template_source(self, template_name, template_dirs=None):
        logger.debug("Trying to load template %s" % str(template_name.split(":")))
        if ":" in template_name:
            username, base, short_name = template_name.split(":")
            try:
                base_model = Base.objects.get(name=base)
                f, template_name = self.get_file(template_name, short_name, base_model)
                return f, template_name
            except Exception, e:
                logger.info("Could not load template %s (%s)" % (template_name, e.message), exc_info=True)
                raise e
        raise TemplateDoesNotExist("Template '%s' not found" % template_name)
