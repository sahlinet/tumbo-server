# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0026_staticfile_accessed'),
    ]

    operations = [
        migrations.AddField(
            model_name='process',
            name='instance',
            field=models.OneToOneField(related_name='processes', null=True, to='core.Instance'),
        ),
    ]
