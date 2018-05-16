# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0032_base_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='base',
            name='source_type',
            field=models.CharField(default=b'DEP', max_length=3, choices=[(b'FS', b'filesystem'), (b'DEP', b'depredicated'), (b'GIT', b'git-repo')]),
        ),
        migrations.AlterField(
            model_name='base',
            name='source',
            field=models.CharField(max_length=100),
        ),
    ]
