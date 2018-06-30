# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0035_auto_20180504_0819'),
    ]

    operations = [
        migrations.AlterField(
            model_name='staticfile',
            name='content',
            field=models.BinaryField(max_length=1000, null=True, blank=True),
        ),
    ]
