# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0034_auto_20180503_1959'),
    ]

    operations = [
        migrations.AlterField(
            model_name='staticfile',
            name='storage',
            field=models.CharField(max_length=2, choices=[(b'FS', b'filesystem'), (b'MO', b'module'), (b'DB', b'database')]),
        ),
    ]
