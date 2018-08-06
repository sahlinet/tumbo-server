# -*- coding: utf-8 -*-

import logging
import random
import re
import StringIO
import urllib
import zipfile
from datetime import datetime, timedelta

import pytz
from configobj import ConfigObj
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import F
from django.dispatch import Signal
from django.template import Template
from django.utils import timezone
from django_extensions.db.fields import (RandomCharField, ShortUUIDField,
                                         UUIDField)
from jsonfield import JSONField

from core.communication import create_vhost, generate_vhost_configuration
from core.executors.remote import (CONFIGURATION_EVENT, SETTINGS_EVENT,
                                   distribute)
from core.plugins import PluginRegistry, call_plugin_func
from sequence_field.fields import SequenceField

logger = logging.getLogger(__name__)

index_template = """{% extends "fastapp/base.html" %}
{% block content %}
{% endblock %}
"""

MODULE_DEFAULT_CONTENT = """def func(self):\n    pass"""


class AuthProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, related_name="authprofile")
    internalid = RandomCharField(length=12, include_alpha=False)

    class Meta:
        app_label = "core"
        db_table = "fastapp_authprofile"

    def __unicode__(self):
        return self.user.username

SOURCE_TYPES = (
    ("FS", 'filesystem'),
    ("DEP", 'depredicated'),
    ("GIT", 'git-repo')
)


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
    revision = models.CharField(max_length=4, blank=True, null=True)
    source_type = models.CharField(max_length=3, choices=SOURCE_TYPES, default="DEP")
    source = models.CharField(max_length=100)
    branch = models.CharField(max_length=30)

    class Meta:
        app_label = "core"
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
    def config(self):
        config_string = StringIO.StringIO()
        config = ConfigObj()

        config['access'] = {}
        config['access']['static_public'] = self.static_public
        config['access']['public'] = self.public

        # execs
        config['modules'] = {}
        for texec in self.apys.all():
            config['modules'][texec.name] = {}
            config['modules'][texec.name]['module'] = texec.name + ".py"
            config['modules'][texec.name]['public'] = texec.public
            config['modules'][texec.name]['schedule'] = texec.schedule
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

    def export(self):
        # create in-memory zipfile
        file_buffer = StringIO.StringIO()
        zf = zipfile.ZipFile(file_buffer, mode='w')

        # add modules
        for apy in self.apys.all():
            logger.info("add %s to zip" % apy.name)
            zf.writestr("%s.py" % apy.name, apy.module.encode("utf-8"))

        # add config
        zf.writestr("app.config", self.config.encode("utf-8"))

        # add index.html
        zf.writestr("index.html", self.content.encode("utf-8"))

        # close zip
        zf.close()

        return file_buffer

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
        except Base.executor.RelatedObjectDoesNotExist, e:
            logger.warn("Executor does not exist")
            return []
        except Exception, e:
            logger.exception(e)
            return []

    # def update(self):
    #     try:
    #         self.executor
    #     except Executor.DoesNotExist:
    #         logger.debug("update executor for base %s" % self)
    #         executor = Executor(base=self)
    #         executor.save()
    #     if not self.executor.is_running():
    #         r = self.executor.update()

    #         # call plugin
    #         logger.info("on_start_base starting...")
    #         call_plugin_func(self, "on_start_base")
    #         logger.info("on_start_base done...")

    #         return r
    #     return None

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

    def save_and_sync(self):
        ready_to_sync.send(self.__class__, instance=self)


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
        app_label = "core"
        db_table = "fastapp_apy"
        unique_together = (("name", "base"),)

    def mark_executed(self):
        if not hasattr(self, "counter"):
            self.counter = Counter(apy=self)
            self.counter.save()
        self.counter.executed = F('executed') + 1
        self.counter.save()

    def mark_failed(self):
        if not hasattr(self, "counter"):
            self.counter = Counter(apy=self)
            self.counter.save()
        self.counter.failed = F('failed') + 1
        self.counter.save()

    def get_exec_url(self):
        return reverse("userland-apy-public-exec", args=[self.base.user.username, self.base.name, self.name]) + "?json="

    def sync(self):
        ready_to_sync.send(self.__class__, instance=self)

    def __str__(self):
        return "%s %s" % (self. name, str(self.id))


class Counter(models.Model):
    apy = models.OneToOneField(Apy, related_name="counter")
    executed = models.IntegerField(default=0)
    failed = models.IntegerField(default=0)

    class Meta:
        app_label = "core"
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
    status = models.CharField(
        max_length=1, choices=TRANSACTION_STATE_CHOICES, default=RUNNING)
    created = models.DateTimeField(default=timezone.now, null=True)
    modified = models.DateTimeField(auto_now=True, null=True)
    tin = JSONField(blank=True, null=True)
    tout = JSONField(blank=True, null=True)
    async = models.BooleanField(default=False)

    class Meta:
        app_label = "core"
        db_table = "fastapp_transaction"

    @property
    def duration(self):
        td = self.modified - self.created
        return td.days * 86400000 + td.seconds * 1000 + td.microseconds / 1000

    def log(self, level, msg):
        logentry = LogEntry(transaction=self)
        logentry.msg = msg
        logentry.level = str(level)
        logentry.save()

    def save(self, *args, **kwargs):
        super(Transaction, self).save(*args, **kwargs)

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
        app_label = "core"
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
        app_label = "core"
        db_table = "fastapp_setting"

"""
Threads -> Processes -> Instances -> Executor -> Base
"""

class Instance(models.Model):
    is_alive = models.BooleanField(default=False)
    uuid = ShortUUIDField(auto=True)
    last_beat = models.DateTimeField(null=True, blank=True)
    executor = models.ForeignKey("Executor", related_name="instances")

    class Meta:
        app_label = "core"
        db_table = "fastapp_instance"

    def mark_down(self):
        self.is_alive = False
        self.save()

    def __str__(self):
        return "Instance: %s" % (self.executor.base.name)


class Host(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        app_label = "core"
        db_table = "fastapp_host"


class Process(models.Model):
    running = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=64, null=True)
    rss = models.IntegerField(default=0)
    version = models.CharField(max_length=10, default=0)
    instance = models.OneToOneField(
        Instance, related_name="process", null=True)

    class Meta:
        app_label = "core"
        db_table = "fastapp_process"

    def is_up(self):
        now = datetime.utcnow().replace(tzinfo=pytz.utc)
        delta = now - self.running
        return delta < timedelta(seconds=10)


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
        app_label = "core"
        db_table = "fastapp_thread"

    name = models.CharField(max_length=64, null=True)
    parent = models.ForeignKey(
        Process, related_name="threads", blank=True, null=True)
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
        app_label = "core"
        db_table = "fastapp_executor"

    def __init__(self, *args, **kwargs):
        super(Executor, self).__init__(*args, **kwargs)
        self.attach_plugins()

    def attach_plugins(self):
        # attach plugins
        plugins = PluginRegistry()
        if not hasattr(self, "plugins"):
            self.plugins = {}
        for plugin in plugins:
            logger.debug("Attach %s.return_to_executor to executor instance '%s'" % (
                plugin.name, self.base.name))
            if hasattr(plugin, "return_to_executor"):
                self.plugins[plugin.name.lower(
                )] = plugin.return_to_executor(self)

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
            logger.info("Instance for '%s' created with id %s" %
                        (self, instance.id))

        kwargs = {}
        if self.port:
            kwargs['service_ports'] = [self.port]

        try:
            logger.info("START Start with implementation %s" %
                        self.implementation)
            self.pid = self.implementation.start(self.pid, **kwargs)
            logger.info("END Start with implementation %s" %
                        self.implementation)
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
            logger.exception("Could not stop")

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
        return self.instances.count() > 1

    def __str__(self):
        return "Executor %s-%s" % (self.base.user.username, self.base.name)


class TransportEndpoint(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    url = models.CharField(max_length=200, blank=False, null=False)
    token = models.CharField(max_length=200, blank=False, null=False)
    override_settings_priv = models.BooleanField(default=False)
    override_settings_pub = models.BooleanField(default=True)

    class Meta:
        app_label = "core"
        db_table = "fastapp_transportendpoint"


ready_to_sync = Signal()


class StaticFile(models.Model):

    class Meta:
        app_label = "core"

    STORAGE = (
        ("FS", 'filesystem'),
        ("MO", 'module'),
        ("DB", 'database'),
    )

    base = models.ForeignKey(Base, related_name="staticfiles")
    name = models.CharField(max_length=300, blank=False, null=False)
    storage = models.CharField(max_length=2, choices=STORAGE)
    rev = models.CharField(max_length=32, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True)
    accessed = models.DateTimeField(null=True)
    content = models.BinaryField(max_length=1000, blank=True, null=True)