# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_auto_20160725_0806'),
    ]

    operations = [
        migrations.AddField(
            model_name='executor',
            name='secret',
            field=django_extensions.db.fields.RandomCharField(include_alpha=False, length=12, editable=False, blank=True),
            preserve_default=True,
        ),
    ]
