# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fastapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='executor',
            name='pid',
            field=models.CharField(max_length=72, null=True),
            preserve_default=True,
        ),
    ]
