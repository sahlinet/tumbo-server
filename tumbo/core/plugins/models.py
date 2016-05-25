# -*- coding: utf-8 -*-

import json
import random
from datetime import datetime, timedelta
from jsonfield import JSONField

from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import serializers

from sequence_field.fields import SequenceField

import logging
logger = logging.getLogger(__name__)

class PluginUserConfig(models.Model):
    plugin_name = models.CharField(max_length=30)
    base = models.ForeignKey("core.Base")
    config = JSONField(default="{}")
