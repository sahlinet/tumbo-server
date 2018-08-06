# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_auto_20180324_2101'),
    ]

    operations = [
        migrations.AlterField(
            model_name='process',
            name='version',
            field=models.CharField(default=0, max_length=10),
        ),
    ]
