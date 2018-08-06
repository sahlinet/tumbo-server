# -*- coding: utf-8 -*-
import logging

from django.db import models
from jsonfield import JSONField

logger = logging.getLogger(__name__)


class PluginUserConfig(models.Model):
    plugin_name = models.CharField(max_length=30)
    base = models.ForeignKey("core.Base")
    config = JSONField(default="{}")

    # class Meta:
    #    app_label = "core"
