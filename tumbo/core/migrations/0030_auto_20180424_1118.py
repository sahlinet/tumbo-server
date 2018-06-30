# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_auto_20180417_1919'),
    ]

    operations = [
        migrations.AddField(
            model_name='staticfile',
            name='content',
            field=models.BinaryField(max_length=300, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='staticfile',
            name='storage',
            field=models.CharField(max_length=2, choices=[(b'FS', b'filesystem'), (b'DR', b'dropbox'), (b'MO', b'module'), (b'DB', b'module')]),
        ),
    ]
