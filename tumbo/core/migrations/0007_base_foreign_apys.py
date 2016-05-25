# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_apy_public'),
    ]

    operations = [
        migrations.AddField(
            model_name='base',
            name='foreign_apys',
            field=models.ManyToManyField(related_name='foreign_base', to='core.Apy'),
            preserve_default=True,
        ),
    ]
