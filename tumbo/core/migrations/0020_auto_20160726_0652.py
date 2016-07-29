# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_executor_secret'),
    ]

    operations = [
        migrations.AlterField(
            model_name='executor',
            name='secret',
            field=django_extensions.db.fields.RandomCharField(length=8, editable=False, blank=True),
            preserve_default=True,
        ),
    ]
