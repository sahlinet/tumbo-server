# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20150116_0749'),
    ]

    operations = [
        migrations.AddField(
            model_name='authprofile',
            name='dropbox_userid',
            field=models.CharField(default=None, max_length=32, null=True, help_text=b'Userid on dropbox'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='authprofile',
            name='access_token',
            field=models.CharField(help_text=b'Access token for dropbox-auth', max_length=72),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='transaction',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
            preserve_default=True,
        ),
    ]
