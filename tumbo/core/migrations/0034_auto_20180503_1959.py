# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0033_auto_20180426_0655'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='authprofile',
            name='dropbox_access_token',
        ),
        migrations.RemoveField(
            model_name='authprofile',
            name='dropbox_userid',
        ),
    ]
