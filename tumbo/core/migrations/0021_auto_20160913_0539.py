# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_auto_20160726_0652'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='apy',
            unique_together=set([('name', 'base')]),
        ),
    ]
