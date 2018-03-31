# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_process_instance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='process',
            name='instance',
            field=models.OneToOneField(related_name='process', null=True, to='core.Instance'),
        ),
    ]
