# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_base_foreign_apys'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='base',
            unique_together=set([('name', 'user')]),
        ),
    ]
