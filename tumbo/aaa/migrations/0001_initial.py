# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def create_group(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    from django.contrib.auth.models import Group
    # TODO: reactivate
    #usergroup = Group.objects.create(name="users")

def revert_group(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.RunPython(create_group, revert_group)
    ]
