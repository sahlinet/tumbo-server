# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'TransportEndpoint'
        db.create_table(u'fastapp_transportendpoint', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('token', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('override_settings_priv', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('override_settings_pub', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'fastapp', ['TransportEndpoint'])

        # to create authtokens for existing users
        from django.contrib.auth import get_user_model
        User = get_user_model()
        from rest_framework.authtoken.models import Token

        for user in User.objects.all():
            Token.objects.get_or_create(user=user)


    def backwards(self, orm):
        # Deleting model 'TransportEndpoint'
        db.delete_table(u'fastapp_transportendpoint')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'fastapp.apy': {
            'Meta': {'object_name': 'Apy'},
            'base': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'apys'", 'null': 'True', 'to': u"orm['fastapp.Base']"}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'module': ('django.db.models.fields.CharField', [], {'default': "'def func(self):\\n    pass'", 'max_length': '16384'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        u'fastapp.authprofile': {
            'Meta': {'object_name': 'AuthProfile'},
            'access_token': ('django.db.models.fields.CharField', [], {'max_length': '72'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'authprofile'", 'unique': 'True', 'to': u"orm['auth.User']"})
        },
        u'fastapp.base': {
            'Meta': {'object_name': 'Base'},
            'content': ('django.db.models.fields.CharField', [], {'default': '\'{% extends "fastapp/index.html" %}\\n{% block content %}\\n{% endblock %}\\n\'', 'max_length': '16384', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'default': '0', 'related_name': "'+'", 'blank': 'True', 'to': u"orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        u'fastapp.counter': {
            'Meta': {'object_name': 'Counter'},
            'apy': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'counter'", 'unique': 'True', 'to': u"orm['fastapp.Apy']"}),
            'executed': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'failed': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'fastapp.executor': {
            'Meta': {'object_name': 'Executor'},
            'base': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'executor'", 'unique': 'True', 'to': u"orm['fastapp.Base']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_instances': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'password': ('django.db.models.fields.CharField', [], {'default': "u'g6pGa8CsGD'", 'max_length': '20'}),
            'pid': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'started': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'fastapp.host': {
            'Meta': {'object_name': 'Host'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'fastapp.instance': {
            'Meta': {'object_name': 'Instance'},
            'executor': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'instances'", 'to': u"orm['fastapp.Executor']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_alive': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_beat': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        u'fastapp.logentry': {
            'Meta': {'object_name': 'LogEntry'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'msg': ('django.db.models.fields.TextField', [], {}),
            'transaction': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'logs'", 'to': u"orm['fastapp.Transaction']"})
        },
        u'fastapp.process': {
            'Meta': {'object_name': 'Process'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'rss': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '7'}),
            'running': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'fastapp.setting': {
            'Meta': {'object_name': 'Setting'},
            'base': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'setting'", 'to': u"orm['fastapp.Base']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '8192'})
        },
        u'fastapp.thread': {
            'Meta': {'object_name': 'Thread'},
            'health': ('django.db.models.fields.CharField', [], {'default': "'SO'", 'max_length': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'threads'", 'null': 'True', 'to': u"orm['fastapp.Process']"})
        },
        u'fastapp.transaction': {
            'Meta': {'object_name': 'Transaction'},
            'apy': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'transactions'", 'to': u"orm['fastapp.Apy']"}),
            'async': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'rid': ('django.db.models.fields.IntegerField', [], {'default': '76623940', 'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'R'", 'max_length': '1'}),
            'tin': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'tout': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'})
        },
        u'fastapp.transportendpoint': {
            'Meta': {'object_name': 'TransportEndpoint'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'override_settings_priv': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'override_settings_pub': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['fastapp']
