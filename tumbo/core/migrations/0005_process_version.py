# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_apy_rev'),
    ]

    operations = [
        migrations.AddField(
            model_name='process',
            name='version',
            field=models.CharField(default=0, max_length=7),
            preserve_default=True,
        ),
    ]
