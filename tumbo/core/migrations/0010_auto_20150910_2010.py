# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_executor_port'),
    ]

    operations = [
        migrations.AddField(
            model_name='executor',
            name='ip',
            field=models.GenericIPAddressField(null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='executor',
            name='ip6',
            field=models.GenericIPAddressField(null=True),
            preserve_default=True,
        ),
    ]
