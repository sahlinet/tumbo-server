# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_extensions.db.fields


def create_field(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    User = apps.get_model("core", "AuthProfile")
    for user in User.objects.all():
        user.save()

def revert_field(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_auto_20160525_0432'),
    ]

    operations = [
        migrations.AddField(
            model_name='authprofile',
            name='internalid',
            field=django_extensions.db.fields.RandomCharField(include_alpha=False, length=12, editable=False, blank=True),
            preserve_default=True,
        ),
        migrations.RunPython(create_field, revert_field)
    ]
