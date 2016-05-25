# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_thread_updated'),
    ]

    operations = [
        migrations.AddField(
            model_name='apy',
            name='schedule',
            field=models.CharField(max_length=64, null=True),
            preserve_default=True,
        ),
    ]
