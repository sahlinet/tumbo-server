# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_staticfile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='staticfile',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
