# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0036_auto_20180520_0533'),
    ]

    operations = [
        migrations.AddField(
            model_name='base',
            name='branch',
            field=models.CharField(default='master', max_length=30),
            preserve_default=False,
        ),
    ]
