# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0030_auto_20180424_1118'),
    ]

    operations = [
        migrations.AddField(
            model_name='base',
            name='revision',
            field=models.CharField(max_length=4, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='staticfile',
            name='storage',
            field=models.CharField(max_length=2, choices=[(b'FS', b'filesystem'), (b'DR', b'dropbox'), (b'MO', b'module'), (b'DB', b'database')]),
        ),
    ]
