# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_process_version'),
    ]

    operations = [
        migrations.AddField(
            model_name='apy',
            name='public',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
