# -*- coding: utf-8 -*-
import logging

from jsonfield import JSONField

from django.db import models


logger = logging.getLogger(__name__)


class PluginUserConfig(models.Model):
    plugin_name = models.CharField(max_length=30)
    base = models.ForeignKey("core.Base")
    config = JSONField(default="{}")
