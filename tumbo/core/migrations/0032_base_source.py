# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0031_auto_20180424_1233'),
    ]

    operations = [
        migrations.AddField(
            model_name='base',
            name='source',
            field=models.CharField(default=b'DEP', max_length=3, choices=[(b'FS', b'filesystem'), (b'DEP', b'depredicated'), (b'GIT', b'git-repo')]),
        ),
    ]
