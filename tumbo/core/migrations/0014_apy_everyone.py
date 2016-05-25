# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_auto_20160329_0731'),
    ]

    operations = [
        migrations.AddField(
            model_name='apy',
            name='everyone',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
