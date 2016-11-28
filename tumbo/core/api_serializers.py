import logging

from rest_framework import serializers
from rest_framework.reverse import reverse

from core.models import Base, Apy, Setting, Counter, TransportEndpoint, Transaction, LogEntry

logger = logging.getLogger(__name__)


class CounterSerializer(serializers.ModelSerializer):

    class Meta:
        model = Counter
        fields = ('executed', 'failed')

class LogSerializer(serializers.ModelSerializer):

    class Meta:
        model = LogEntry
        fields = ('level', 'msg', 'created', )


class TransactionSerializer(serializers.ModelSerializer):
    logs = LogSerializer(many=True, read_only=True)

    class Meta:
        model = Transaction
        fields = ('rid', 'tin', 'tout', 'status', 'created', 'modified', 'async', 'logs', )


class ApySerializer(serializers.ModelSerializer):
    counter = CounterSerializer(many=False, read_only=True)
    #mynum = serializers.SerializerMethodField(method_name="get_id")

    def get_id(self, obj):
        return obj.id

    class Meta:
        model = Apy
        fields = ('name', 'module', 'counter', 'description', 'public', 'schedule', 'everyone')

    def save(self, *args, **kwargs):
        obj = super(ApySerializer, self).save(*args, **kwargs)
        obj.sync(**kwargs)


class PublicApySerializer(serializers.ModelSerializer):
    """
    Return all Apy objects which are made public. Enrich
    """
    first_lastname = serializers.SerializerMethodField(method_name="creator")
    base = serializers.SerializerMethodField(method_name="base_name")
    url = serializers.SerializerMethodField(method_name="detail_view")

    class Meta:
        model = Apy
        fields = ('id', 'name', 'module', 'description',
                  'first_lastname', 'url', 'base')

    def creator(self, obj):
        try:
            user = obj.base.user
            return user.first_name + " " + user.last_name
        except Base.DoesNotExist, e:
            logger.warn(e)

    def base_name(self, obj):
        return obj.base.name

    def detail_view(self, obj):
        return reverse('public-apy-detail', args=[obj.pk],
                       request=self.context['request'])


class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setting
        fields = ('id', 'key', 'value', 'public')


class TransportEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransportEndpoint
        fields = ('id', 'url', 'override_settings_priv',
                  'override_settings_pub', 'token')


class BaseSerializer(serializers.ModelSerializer):
    apys = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    full_name = serializers.SerializerMethodField()
    state = serializers.ReadOnlyField()
    executors = serializers.ReadOnlyField()
    foreign_apys = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name='public-apy-detail'
    )

    def get_full_name(self, obj):
        return "%s/%s" % (obj.user.username, obj.name)

    class Meta:
        model = Base
        fields = ('id', 'name', 'full_name', 'state', 'uuid',
                  'executors', 'content', 'foreign_apys', 'public', 'static_public', 'apys')

    #def save(self, obj, **kwargs):
        #super(BaseSerializer, self).save(obj, *args, **kwargs)
        #obj.save_and_sync(**kwargs)
