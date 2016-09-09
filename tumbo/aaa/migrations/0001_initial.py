# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

def create_group(apps, schema_editor):
    from django.contrib.auth.models import Group
    usergroup = Group.objects.create(name="users")

def revert_group(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.RunPython(create_group, revert_group)
    ]
