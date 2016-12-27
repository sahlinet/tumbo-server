# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_auto_20161124_0742'),
    ]

    operations = [
        migrations.AddField(
            model_name='staticfile',
            name='accessed',
            field=models.DateTimeField(null=True),
        ),
    ]
