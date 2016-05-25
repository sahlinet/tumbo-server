# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import core.models
import jsonfield.fields
from django.conf import settings
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Apy',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('module', models.CharField(default=b'def func(self):\n    pass', max_length=16384)),
                ('description', models.CharField(max_length=1024, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AuthProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('access_token', models.CharField(max_length=72)),
                ('user', models.OneToOneField(related_name='authprofile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Base',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=32)),
                ('uuid', django_extensions.db.fields.UUIDField(editable=False, name=b'uuid', blank=True)),
                ('content', models.CharField(default=b'{% extends "fastapp/base.html" %}\n{% block content %}\n{% endblock %}\n', max_length=16384, blank=True)),
                ('public', models.BooleanField(default=False)),
                ('user', models.ForeignKey(related_name='bases', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Counter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('executed', models.IntegerField(default=0)),
                ('failed', models.IntegerField(default=0)),
                ('apy', models.OneToOneField(related_name='counter', to='core.Apy')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Executor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('num_instances', models.IntegerField(default=1)),
                ('pid', models.CharField(max_length=10, null=True)),
                ('password', models.CharField(default=core.models.default_pass, max_length=20)),
                ('started', models.BooleanField(default=False)),
                ('base', models.OneToOneField(related_name='executor', to='core.Base')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Host',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Instance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_alive', models.BooleanField(default=False)),
                ('uuid', django_extensions.db.fields.ShortUUIDField(editable=False, name=b'uuid', blank=True)),
                ('last_beat', models.DateTimeField(null=True, blank=True)),
                ('executor', models.ForeignKey(related_name='instances', to='core.Executor')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LogEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('level', models.CharField(max_length=2, choices=[(b'10', b'DEBUG'), (b'20', b'INFO'), (b'30', b'WARNING'), (b'40', b'ERROR'), (b'50', b'CRITICAL')])),
                ('msg', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Process',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('running', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=64, null=True)),
                ('rss', models.IntegerField(default=0, max_length=7)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Setting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=128)),
                ('value', models.CharField(max_length=8192)),
                ('public', models.BooleanField(default=False)),
                ('base', models.ForeignKey(related_name='setting', to='core.Base')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Thread',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, null=True)),
                ('health', models.CharField(default=b'SO', max_length=2, choices=[(b'SA', b'Started'), (b'SO', b'Stopped'), (b'NC', b'Not connected')])),
                ('parent', models.ForeignKey(related_name='threads', blank=True, to='core.Process', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('rid', models.IntegerField(default=core.models.create_random, serialize=False, primary_key=True)),
                ('status', models.CharField(default=b'R', max_length=1, choices=[(b'R', b'RUNNING'), (b'F', b'FINISHED'), (b'T', b'TIMEOUT')])),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified', models.DateTimeField(auto_now=True, null=True)),
                ('tin', jsonfield.fields.JSONField(null=True, blank=True)),
                ('tout', jsonfield.fields.JSONField(null=True, blank=True)),
                ('async', models.BooleanField(default=False)),
                ('apy', models.ForeignKey(related_name='transactions', to='core.Apy')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TransportEndpoint',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.CharField(max_length=200)),
                ('token', models.CharField(max_length=200)),
                ('override_settings_priv', models.BooleanField(default=False)),
                ('override_settings_pub', models.BooleanField(default=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='logentry',
            name='transaction',
            field=models.ForeignKey(related_name='logs', to='core.Transaction'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='apy',
            name='base',
            field=models.ForeignKey(related_name='apys', blank=True, to='core.Base', null=True),
            preserve_default=True,
        ),
    ]
