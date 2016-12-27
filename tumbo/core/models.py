# -*- coding: utf-8 -*-

import urllib
import StringIO
import gevent
import json
import pytz
import random
import zipfile
import re

from configobj import ConfigObj
from datetime import datetime, timedelta
from jsonfield import JSONField
from sequence_field.fields import SequenceField

from django.core.urlresolvers import reverse
from django.db import models, transaction
from django.template import Template
from django_extensions.db.fields import UUIDField, ShortUUIDField, RandomCharField
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver, Signal
from django.db.models import F
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import serializers
from django.utils import timezone

from core.queue import generate_vhost_configuration, create_vhost
from core.executors.remote import distribute, CONFIGURATION_EVENT, SETTINGS_EVENT
from core.utils import Connection
from core.plugins import call_plugin_func
from core.plugins import PluginRegistry


import logging
logger = logging.getLogger(__name__)

index_template = """{% extends "fastapp/base.html" %}
{% block content %}
{% endblock %}
"""


class AuthProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="authprofile")
    dropbox_access_token = models.CharField(max_length=72, help_text="Access token for dropbox-auth")
    internalid = RandomCharField(length=12, include_alpha=False)
    dropbox_userid = models.CharField(max_length=32,
                                      help_text="Userid on dropbox",
                                      default=None, null=True)

    class Meta:
        db_table = "fastapp_authprofile"

    def __unicode__(self):
        return self.user.username


class Base(models.Model):
    name = models.CharField(max_length=32)
    uuid = UUIDField(auto=True)
    content = models.CharField(max_length=16384,
                               blank=True,
                               default=index_template)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='bases')
    public = models.BooleanField(default=False)
    static_public = models.BooleanField(default=False)

    foreign_apys = models.ManyToManyField("Apy", related_name="foreign_base")

    frontend_host = models.CharField(max_length=40,
                               blank=True, null=True,
                               default=None)

    class Meta:
        db_table = "fastapp_base"
        unique_together = (("name", "user"),)

    @property
    def url(self):
        return "/fastapp/%s" % self.name

    @property
    def shared(self):
        return "/fastapp/%s/index/?shared_key=%s" % (
            self.name,
            urllib.quote(self.uuid))

    @property
    def auth_token(self):
        return self.user.authprofile.dropbox_access_token

    @property
    def config(self):
        config_string = StringIO.StringIO()
        config = ConfigObj()

        # execs
        config['modules'] = {}
        for texec in self.apys.all():
            config['modules'][texec.name] = {}
            config['modules'][texec.name]['module'] = texec.name+".py"
            config['modules'][texec.name]['public'] = texec.public
            if texec.description:
                config['modules'][texec.name]['description'] = texec.description
            else:
                config['modules'][texec.name]['description'] = ""

        # settings
        config['settings'] = {}
        for setting in self.setting.all():
            if setting.public:
                config['settings'][setting.key] = {
                    'value': setting.value,
                    'public': setting.public
                }
            else:
                config['settings'][setting.key] = {
                    'value': "",
                    'public': setting.public
                }
        config.write(config_string)
        return config_string.getvalue()

    def refresh(self, put=False):
        connection = Connection(self.user.authprofile.dropbox_access_token)
        template_name = "%s/index.html" % self.name
        template_content = connection.get_file_content(template_name)
        self.content = template_content

#    def refresh_execs(self, exec_name=None, put=False):
#        from core.utils import Connection, NotFound
#        # execs
#        connection = Connection(self.user.authprofile.dropbox_access_token)
#        app_config = "%s/app.config" % self.name
#        config = ConfigParser.RawConfigParser()
#        config.readfp(io.BytesIO(connection.get_file_content(app_config)))
#        if put:
#            if exec_name:
#                connection.put_file("%s/%s.py" % (self.name, exec_name),
#                                self.execs.get(name=exec_name).module)
#                connection.put_file(app_config, self.config)
#            else:
#                raise Exception("exec_name not specified")
#        else:
#            for name in config.sections():
#                module_name = config.get(name, "module")
#                try:
#                    module_content = connection.get_file_content("%s/%s" % (self.name, module_name))
#                except NotFound:
#                    try:
#                        Exec.objects.get(name=module_name, base=self).delete()
#                    except Exec.DoesNotExist, e:
#                        self.save()
#
#                # save new exec
#                app_exec_model, created = Apy.objects.get_or_create(base=self, name=name)
#                app_exec_model.module = module_content
#                app_exec_model.save()
#
#            # delete old exec
#            for local_exec in Apy.objects.filter(base=self).values('name'):
#                if local_exec['name'] in config.sections():
#                    logger.warn()
#                else:
#                    Apy.objects.get(base=self, name=local_exec['name']).delete()

    def export(self):
        # create in-memory zipfile
        buffer = StringIO.StringIO()
        zf = zipfile.ZipFile(buffer, mode='w')

        # add modules
        for apy in self.apys.all():
            logger.info("add %s to zip" % apy.name)
            zf.writestr("%s.py" % apy.name, apy.module.encode("utf-8"))

        # add static files
        try:
            dropbox_connection = Connection(self.auth_token)

            try:
                zf = dropbox_connection.directory_zip(
                            "%s/%s/static" % (self.user.username, self.name), zf
                )
            except Exception, e:
               logger.warn(e)
        except AuthProfile.DoesNotExist, e:
            logger.warn(e)
        except Exception, e:
            logger.warn(e.__class__)
            logger.exception(e)

        # add config
        zf.writestr("app.config", self.config.encode("utf-8"))

        # add index.html
        zf.writestr("index.html", self.content.encode("utf-8"))

        # close zip
        zf.close()

        return buffer

    def template(self, context):
        t = Template(self.content)
        return t.render(context)

    @property
    def state(self):
        """
        States:
            - DELETING
            - DESTROYED
            - STOPPED
            - CREATING
            - STARTING
            - STARTED
            - INITIALIZING
            - RUNNING

        Restart:
            - RUNNING
            - STOPPED
            - STARTING
            - STARTED
            - RUNNING

        Creation:
            - CREATING
            - STARTING
            - STARTED
            - INITIALIZING
            - RUNNING

        Destroy:
            - RUNNING / STOPPED
            - DELETING
            - DESTROYED
        """

        try:
            return self.executor.is_running()
        except (IndexError, Executor.DoesNotExist):
            return False

    @property
    def executors(self):
        try:
            if self.executor.pid is None:
                return []
            return [
                {
                    'pid': self.executor.pid,
                    'port': self.executor.port,
                    'ip': self.executor.ip,
                    'ip6': self.executor.ip6,
                    'plugins': self.executor.plugins
                }
            ]
        except Exception, e:
            logger.exception(e)
            return []

    def start(self):
        try:
            self.executor
        except Executor.DoesNotExist:
            logger.debug("create executor for base %s" % self)
            executor = Executor(base=self)
            executor.save()
        if not self.executor.is_running():
            r = self.executor.start()

            # call plugin
            logger.info("on_start_base starting...")
            call_plugin_func(self, "on_start_base")
            logger.info("on_start_base done...")

            return r
        return None

    def stop(self):
        return self.executor.stop()

    def destroy(self):
        call_plugin_func(self, "on_destroy_base")
        return self.executor.destroy()

    def __str__(self):
        return "<Base: %s>" % self.name

    def save_and_sync(self, **kwargs):
        ready_to_sync.send(self.__class__, instance=self)

    #def save(self, **kwargs):
    #    logger.debug("create executor for base %s" % self)
    #    print self.__dict__
    #    if not hasattr(self, 'executor'):
    #        executor = Executor(base=self)
    #        executor.save()
    #    self.save(**kwargs)

MODULE_DEFAULT_CONTENT = """def func(self):\n    pass"""


class Apy(models.Model):
    name = models.CharField(max_length=64)
    module = models.CharField(max_length=16384, default=MODULE_DEFAULT_CONTENT)
    base = models.ForeignKey(Base, related_name="apys", blank=True, null=True)
    description = models.CharField(max_length=1024, blank=True, null=True)
    public = models.BooleanField(default=False)
    everyone = models.BooleanField(default=False)
    rev = models.CharField(max_length=32, blank=True, null=True)

    schedule = models.CharField(max_length=64, null=True, blank=True)

    class Meta:
        db_table = "fastapp_apy"
        unique_together = (("name", "base"),)

    def mark_executed(self):
        if not hasattr(self, "counter"):
            self.counter = Counter(apy=self)
            self.counter.save()
        self.counter.executed = F('executed')+1
        self.counter.save()

    def mark_failed(self):
        if not hasattr(self, "counter"):
            self.counter = Counter(apy=self)
            self.counter.save()
        self.counter.failed = F('failed')+1
        self.counter.save()

    def get_exec_url(self):
        return reverse("userland-apy-public-exec", args=[self.base.user.username, self.base.name, self.name]) + "?json="

    def sync(self, **kwargs):
        ready_to_sync.send(self.__class__, instance=self)

    def __str__(self):
        return "%s %s" % (self. name, str(self.id))


class Counter(models.Model):
    apy = models.OneToOneField(Apy, related_name="counter")
    executed = models.IntegerField(default=0)
    failed = models.IntegerField(default=0)

    class Meta:
        db_table = "fastapp_counter"

RUNNING = "R"
FINISHED = "F"
TIMEOUT = "T"

TRANSACTION_STATE_CHOICES = (
    ('R', 'RUNNING'),
    ('F', 'FINISHED'),
    ('T', 'TIMEOUT'),
)


def create_random():
    rand = random.SystemRandom().randint(10000000, 99999999)
    return rand



class Transaction(models.Model):
    rid = models.IntegerField(primary_key=True, default=create_random)
    apy = models.ForeignKey(Apy, related_name="transactions")
    status = models.CharField(max_length=1, choices=TRANSACTION_STATE_CHOICES, default=RUNNING)
    created = models.DateTimeField(default=timezone.now, null=True)
    modified = models.DateTimeField(auto_now=True, null=True)
    tin = JSONField(blank=True, null=True)
    tout = JSONField(blank=True, null=True)
    async = models.BooleanField(default=False)

    class Meta:
        db_table = "fastapp_transaction"

    @property
    def duration(self):
        td = self.modified - self.created
        return td.days*86400000 + td.seconds*1000 + td.microseconds/1000

    def log(self, level, msg):
        logentry = LogEntry(transaction=self)
        logentry.msg = msg
        logentry.level = str(level)
        logentry.save()

    def save(self, *args, **kwargs):
        super(self.__class__, self).save(*args, **kwargs)

    @property
    def apy_name(self):
        return self.apy.name

    @property
    def base_name(self):
        return self.apy.base.name

LOG_LEVELS = (
    ("10", 'DEBUG'),
    ("20", 'INFO'),
    ("30", 'WARNING'),
    ("40", 'ERROR'),
    ("50", 'CRITICAL')
)


class LogEntry(models.Model):
    transaction = models.ForeignKey(Transaction, related_name="logs")
    created = models.DateTimeField(auto_now_add=True, null=True)
    level = models.CharField(max_length=2, choices=LOG_LEVELS)
    msg = models.TextField()

    class Meta:
        db_table = "fastapp_logentry"

    def level_verbose(self):
        return dict(LOG_LEVELS)[self.level]

    @property
    def slevel(self):
        return self.level_verbose()

    @property
    def tid(self):
        return self.transaction.rid


class Setting(models.Model):
    base = models.ForeignKey(Base, related_name="setting")
    key = models.CharField(max_length=128)
    value = models.CharField(max_length=8192)
    public = models.BooleanField(default=False, null=False, blank=False)

    class Meta:
        db_table = "fastapp_setting"


class Instance(models.Model):
    is_alive = models.BooleanField(default=False)
    uuid = ShortUUIDField(auto=True)
    last_beat = models.DateTimeField(null=True, blank=True)
    executor = models.ForeignKey("Executor", related_name="instances")

    class Meta:
        db_table = "fastapp_instance"


    def mark_down(self):
        self.is_alive = False
        self.save()

    def __str__(self):
        return "Instance: %s" % (self.executor.base.name)


class Host(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        db_table = "fastapp_host"


class Process(models.Model):
    running = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=64, null=True)
    rss = models.IntegerField(default=0)
    version = models.CharField(max_length=7, default=0)

    class Meta:
        db_table = "fastapp_process"

    def is_up(self):
        now = datetime.utcnow().replace(tzinfo = pytz.utc)
        delta = now - self.running
        return (delta < timedelta(seconds=10))


class Thread(models.Model):
    STARTED = "SA"
    STOPPED = "SO"
    NOT_CONNECTED = "NC"
    HEALTH_STATE_CHOICES = (
        (STARTED, "Started"),
        (STOPPED, "Stopped"),
        (NOT_CONNECTED, "Not connected")
        )

    class Meta:
        db_table = "fastapp_thread"

    name = models.CharField(max_length=64, null=True)
    parent = models.ForeignKey(Process, related_name="threads", blank=True, null=True)
    health = models.CharField(max_length=2,
                            choices=HEALTH_STATE_CHOICES,
                            default=STOPPED)
    updated = models.DateTimeField(auto_now=True, null=True)

    def started(self):
        self.health = Thread.STARTED
        self.save()

    def not_connected(self):
        self.health = Thread.NOT_CONNECTED
        self.save()


def default_pass():
    return get_user_model().objects.make_random_password()


class Executor(models.Model):
    base = models.OneToOneField(Base, related_name="executor")
    num_instances = models.IntegerField(default=1)
    pid = models.CharField(max_length=72, null=True)
    password = models.CharField(max_length=20, default=default_pass)
    started = models.BooleanField(default=False)
    ip = models.GenericIPAddressField(null=True)
    ip6 = models.GenericIPAddressField(null=True)
    secret = RandomCharField(length=8, include_alpha=True, editable=True)

    port = SequenceField(
        key='test.sequence.1',
        template='1%NNNN',
        auto=True,
        null=True
    )

    class Meta:
        db_table = "fastapp_executor"

    def __init__(self, *args, **kwargs):
        super(Executor, self ).__init__(*args, **kwargs)
        self.attach_plugins()

    def attach_plugins(self):
        # attach plugins
        plugins = PluginRegistry()
        if not hasattr(self, "plugins"):
            self.plugins = {}
        for plugin in plugins:
            logger.debug("Attach %s.return_to_executor to executor instance '%s'" % (plugin.name, self.base.name))
            if hasattr(plugin, "return_to_executor"):
                self.plugins[plugin.name.lower()] = plugin.return_to_executor(self)

    @property
    def vhost(self):
        return generate_vhost_configuration(self.base.user.username,
                                            self.base.name)

    @property
    def implementation(self):
        s_exec = getattr(settings, 'TUMBO_WORKER_IMPLEMENTATION',
                                   'core.executors.worker_engines.spawnproc.SpawnExecutor')
        regex = re.compile("(.*)\.(.*)")
        r = regex.search(s_exec)
        s_mod = r.group(1)
        s_cls = r.group(2)
        m = __import__(s_mod, globals(), locals(), [s_cls])
        try:
            cls = m.__dict__[s_cls]
            return cls(
                vhost=self.vhost,
                base_name=self.base.name,
                username=self.base.name,
                password=self.password,
                secret=self.secret,
                executor=self
                )
        except KeyError, e:
            logger.error("Could not load %s" % s_exec)
            raise e

    def start(self):
        logger.info("Start manage.py start_worker")
        create_vhost(self.base)

        try:
            instance = Instance.objects.get(executor=self)
            logger.info("Instance found with id %s" % instance.id)
        except Instance.DoesNotExist, e:
            instance = Instance(executor=self)
            instance.save()
            logger.info("Instance for '%s' created with id %s" % (self, instance.id))

        kwargs = {}
        if self.port:
            kwargs['service_ports'] = [self.port]

        try:
            logger.info("START Start with implementation %s" % self.implementation)
            self.pid = self.implementation.start(self.pid, **kwargs)
            logger.info("END Start with implementation %s" % self.implementation)
        except Exception, e:
            raise e

        logger.info("%s: worker started with pid %s" % (self, self.pid))

        self.started = True

        ips = self.implementation.addresses(self.pid, port=self.port)
        logger.info("ips: %s" % str(ips))
        self.ip = ips['ip']
        self.ip6 = ips['ip6']

        self.save()
        logger.info("%s: worker saved with pid %s" % (self, self.pid))

    def stop(self):
        logger.info("Stop worker with PID %s" % self.pid)

        self.implementation.stop(self.pid)

        pid = str(self.pid)

        # Threads
        try:
            process = Process.objects.get(name=self.vhost)
            for thread in process.threads.all():
                thread.delete()
        except Exception:
            logger.exception()

        self.save()
        logger.info("Stopped worker with PID %s" % pid)

    def restart(self):
        self.stop()
        self.start()

    def destroy(self):
        self.implementation.destroy(self.pid)
        self.pid = None
        self.started = False
        self.save()

    def is_running(self):
        # if no pid, return directly false
        if not self.pid:
            return False

        # if pid, check
        return self.implementation.state(self.pid)

    def is_alive(self):
        return self.instances.count()>1

    def __str__(self):
        return "Executor %s-%s" % (self.base.user.username, self.base.name)


class TransportEndpoint(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    url = models.CharField(max_length=200, blank=False, null=False)
    token = models.CharField(max_length=200, blank=False, null=False)
    override_settings_priv = models.BooleanField(default=False)
    override_settings_pub = models.BooleanField(default=True)

    class Meta:
        db_table = "fastapp_transportendpoint"

ready_to_sync = Signal()


@receiver(ready_to_sync, sender=Base)
def initialize_on_storage(sender, *args, **kwargs):
    instance = kwargs['instance']
    # TODO: If a user connects his dropbox after creating a base, it should be initialized anyway.

    connection = Connection(instance.user.authprofile.dropbox_access_token)
    #if not kwargs.get('created'):
    #    connection.put_file("%s/index.html" % (instance.name), instance.content)
    #    return
    logger.info("initialize_on_storage for Base '%s'" % instance.name)
    logger.info(kwargs)
    try:
        connection.create_folder("%s/%s" % (instance.user.username, instance.name))
    except Exception, e:
        pass
        #if "already exists" in e['body']['error']:
        #    pass
        #else:
        #    logger.exception(e)

    connection.put_file("%s/%s/app.config" % (instance.user.username, instance.name), instance.config)
    connection.put_file("%s/%s/index.html" % (instance.user.username, instance.name), instance.content)


@receiver(ready_to_sync, sender=Apy)
def synchronize_to_storage(sender, *args, **kwargs):
    instance = kwargs['instance']
    try:
        connection = Connection(instance.base.user.authprofile.dropbox_access_token)
        result = connection.put_file("%s/%s/%s.py" % (instance.base.user.username, instance.base.name,
                                                   instance.name),
                                     instance.module)
        queryset = Apy.objects.all()
        #print result['rev']
        #queryset.get(pk=instance.pk).update(rev=result['rev'])
        instance.rev=result['rev']
        instance.save()

        # update app.config for saving description
        result = connection.put_file("%s/%s/app.config" % (instance.base.user.username, 
                                     instance.base.name),
                                     instance.base.config)
    except Exception, e:
        logger.exception(e)

    if instance.base.state:
        distribute(CONFIGURATION_EVENT, serializers.serialize("json",
                                                              [instance, ]),
                   generate_vhost_configuration(instance.base.user.username,
                                                instance.base.name),
                   instance.base.name,
                   instance.base.executor.password
                   )


# Distribute signals
@receiver(post_save, sender=Setting)
def send_to_workers(sender, *args, **kwargs):
    instance = kwargs['instance']
    if instance.base.state:
        distribute(SETTINGS_EVENT, json.dumps({instance.key: instance.value}),
                   generate_vhost_configuration(instance.base.user.username,
                                                instance.base.name),
                   instance.base.name,
                   instance.base.executor.password
                   )


@receiver(post_save, sender=Base)
def setup_base(sender, *args, **kwargs):
    instance = kwargs['instance']

    # create executor instance if none
    try:
        instance.executor
    except Executor.DoesNotExist:
        logger.debug("create executor for base %s" % instance)
        executor = Executor(base=instance)
        executor.save()


@receiver(post_delete, sender=Base)
def base_to_storage_on_delete(sender, *args, **kwargs):
    instance = kwargs['instance']
    try:
        connection = Connection(instance.user.authprofile.dropbox_access_token)
        gevent.spawn(connection.delete_file("%s/%s" % (instance.user.username, instance.name)))
    except Exception, e:
        logger.error("error in base_to_storage_on_delete")
        logger.exception(e)


class StaticFile(models.Model):

    STORAGE= (
        ("FS", 'filesystem'),
        ("DR", 'dropbox'),
        ("MO", 'module'),
    )

    base = models.ForeignKey(Base, related_name="staticfiles")
    name = models.CharField(max_length=300, blank=False, null=False)
    storage = models.CharField(max_length=2, choices=STORAGE)
    rev = models.CharField(max_length=32, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True)
    accessed = models.DateTimeField(null=True)

    def __str__(self):
        return "%s://%s" % (self.get_storage_display(), self.name)


@receiver(post_delete, sender=Apy)
def synchronize_to_storage_on_delete(sender, *args, **kwargs):
    instance = kwargs['instance']
    from utils import NotFound
    try:
        connection = Connection(instance.base.user.authprofile.dropbox_access_token)
        gevent.spawn(connection.put_file("%s/%s/app.config" % (
                                         instance.base.user.username,
                                         instance.base.name),
                                         instance.base.config))
        gevent.spawn(connection.delete_file("%s/%s.py" % (instance.base.name,
                                            instance.name)))
    except NotFound:
        logger.exception("error in synchronize_to_storage_on_delete")
    except Base.DoesNotExist:
        # if post_delete is triggered from base.delete()
        logger.debug("post_delete signal triggered by base.delete(), can be ignored")
    except Exception, e:
        logger.error("error in synchronize_to_storage_on_delete")
        logger.exception(e)
