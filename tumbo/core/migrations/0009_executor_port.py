# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import sequence_field.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_auto_20150703_1033'),
    ]

    operations = [
        migrations.AddField(
            model_name='executor',
            name='port',
            field=sequence_field.fields.SequenceField(help_text='The value does not match the specified pattern', null=True),
            preserve_default=True,
        ),
    ]
