# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_base_frontend_host'),
    ]

    operations = [
        migrations.CreateModel(
            name='StaticFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=300)),
                ('storage', models.CharField(max_length=2, choices=[(b'FS', b'filesystem'), (b'DR', b'dropbox'), (b'MO', b'module')])),
                ('rev', models.CharField(max_length=32, null=True, blank=True)),
                ('updated', models.DateTimeField(auto_now=True, auto_now_add=True)),
                ('base', models.ForeignKey(related_name='staticfiles', to='core.Base')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
