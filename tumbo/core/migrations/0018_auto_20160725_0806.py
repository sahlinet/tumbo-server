# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_authprofile_internalid'),
    ]

    operations = [
        migrations.RenameField(
            model_name='authprofile',
            old_name='access_token',
            new_name='dropbox_access_token',
        ),
    ]
