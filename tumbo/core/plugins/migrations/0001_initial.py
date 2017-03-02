# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0026_staticfile_accessed'),
    ]

    operations = [
        migrations.CreateModel(
            name='PluginUserConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('plugin_name', models.CharField(max_length=30)),
                ('config', jsonfield.fields.JSONField(default=b'{}')),
                ('base', models.ForeignKey(to='core.Base')),
            ],
        ),
    ]
