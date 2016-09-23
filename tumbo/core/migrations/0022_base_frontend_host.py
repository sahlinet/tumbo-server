# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_auto_20160913_0539'),
    ]

    operations = [
        migrations.AddField(
            model_name='base',
            name='frontend_host',
            field=models.CharField(default=None, max_length=40, null=True, blank=True),
            preserve_default=True,
        ),
    ]
