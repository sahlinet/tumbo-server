# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_auto_20161124_0740'),
    ]

    operations = [
        migrations.AlterField(
            model_name='process',
            name='rss',
            field=models.IntegerField(default=0),
        ),
    ]
