# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_base_static_public'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='apy',
            table='fastapp_apy',
        ),
        migrations.AlterModelTable(
            name='authprofile',
            table='fastapp_authprofile',
        ),
        migrations.AlterModelTable(
            name='base',
            table='fastapp_base',
        ),
        migrations.AlterModelTable(
            name='counter',
            table='fastapp_counter',
        ),
        migrations.AlterModelTable(
            name='executor',
            table='fastapp_executor',
        ),
        migrations.AlterModelTable(
            name='host',
            table='fastapp_host',
        ),
        migrations.AlterModelTable(
            name='instance',
            table='fastapp_instance',
        ),
        migrations.AlterModelTable(
            name='logentry',
            table='fastapp_logentry',
        ),
        migrations.AlterModelTable(
            name='process',
            table='fastapp_process',
        ),
        migrations.AlterModelTable(
            name='setting',
            table='fastapp_setting',
        ),
        migrations.AlterModelTable(
            name='thread',
            table='fastapp_thread',
        ),
        migrations.AlterModelTable(
            name='transaction',
            table='fastapp_transaction',
        ),
        migrations.AlterModelTable(
            name='transportendpoint',
            table='fastapp_transportendpoint',
        ),
    ]
