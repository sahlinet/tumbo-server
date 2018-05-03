# -*- coding: utf-8 -*-

import json
import logging
import random
import re
import StringIO
import urllib
import zipfile
from datetime import datetime, timedelta

import gevent
import pytz
from configobj import ConfigObj
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import serializers
from django.core.urlresolvers import reverse
from django.db import models, transaction
from django.db.models import F
from django.db.models.signals import post_delete, post_save
from django.dispatch import Signal, receiver
from django.template import Template
from django.utils import timezone
from django_extensions.db.fields import (RandomCharField, ShortUUIDField,
                                         UUIDField)
from jsonfield import JSONField
from sequence_field.fields import SequenceField

from core.communication import create_vhost, generate_vhost_configuration
from core.executors.remote import (CONFIGURATION_EVENT, SETTINGS_EVENT,
                                   distribute)
from core.models import *
from core.plugins import PluginRegistry, call_plugin_func
from core.storage import Storage

logger = logging.getLogger(__name__)


# Distribute settings
@receiver(post_save, sender=Setting)
def send_to_workers(sender, *args, **kwargs):
    instance = kwargs['instance']
    storage = Storage.factory()(instance)
    storage._save_config()

    if instance.base.state:
        distribute(SETTINGS_EVENT, json.dumps({instance.key: instance.value}),
                   generate_vhost_configuration(instance.base.user.username,
                                                instance.base.name),
                   instance.base.name,
                   instance.base.executor.password
                   )


@receiver(post_save, sender=Base)
def setup_base(sender, *args, **kwargs):
    instance = kwargs['instance']

    # create executor instance if none
    try:
        instance.executor
    except Executor.DoesNotExist:
        logger.debug("create executor for base %s" % instance)
        executor = Executor(base=instance)
        executor.save()


@receiver(post_delete, sender=Apy)
def synchronize_to_storage_on_delete(sender, *args, **kwargs):
    instance = kwargs['instance']
    from utils import NotFound
    try:
        storage = Storage.factory()(instance)
        storage.delete("%s/%s.py" % (instance.base.name, instance.name))
    except NotFound:
        logger.exception("error in synchronize_to_storage_on_delete")
    except Base.DoesNotExist:
        # if post_delete is triggered from base.delete()
        logger.debug(
            "post_delete signal triggered by base.delete(), can be ignored")
    except Exception, e:
        logger.error("error in synchronize_to_storage_on_delete")
        logger.exception(e)


@receiver(ready_to_sync, sender=Base)
def initialize_on_storage(sender, *args, **kwargs):
    instance = kwargs['instance']

    logger.info("initialize_on_storage for Base '%s'" % instance.name)
    logger.info(kwargs)
    try:
        storage = Storage.factory()(instance)
        storage.create_folder("%s/%s")
    except Exception:
        pass


@receiver(ready_to_sync, sender=Apy)
def synchronize_to_storage(sender, *args, **kwargs):
    instance = kwargs['instance']
    try:
        storage = Storage.factory()(instance)
        result = storage.put("%s/%s.py" %
                             (instance.base.name, instance.name), instance.module)

        # add revision for the storage modules
        if result:
            instance.rev = result['rev']
            instance.save()

    except Exception, e:
        logger.exception(e)

    if instance.base.state:
        distribute(CONFIGURATION_EVENT, serializers.serialize("json",
                                                              [instance, ]),
                   generate_vhost_configuration(instance.base.user.username,
                                                instance.base.name),
                   instance.base.name,
                   instance.base.executor.password
                   )
