"""
needs SQLAlchemy==1.0.12
PSQL >9.3

ADD Quota "https://gist.github.com/javisantana/1277714"

"""

import os
import logging
import datetime
import inspect

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.schema import CreateSchema
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.pool import NullPool

from django.conf import settings

from core.plugins import Plugin
from core.plugins.singleton import Singleton
from core.plugins.registry import register_plugin


logger = logging.getLogger(__name__)

Base = declarative_base()


class DataObject(Base):

    __tablename__ = 'data_table'

    id = Column(Integer, primary_key=True)
    created_on = Column(DateTime, default=datetime.datetime.now)
    data = Column(JSON)


class DataStore(object):

    ENGINE = 'sqlite:///:memory:'

    def __init__(self, schema=None, password=None, *args, **kwargs):
        if schema:
            self.schema = schema.replace("-", "_")
        else:
            self.schema = schema
        self.kwargs = kwargs
        logger.info("Working with schema: %s" % schema)
        logger.info("Working with config: %s" % str(kwargs))

        self.password = password

        # set schema for table creation
        DataObject.__table__.schema = self.schema

        # create session with engine
        self.engine = create_engine(self.__class__.ENGINE % kwargs, echo=False, poolclass=NullPool)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # set schema for sql executions
        self._execute("SET search_path TO %s" % self.schema)
        self._commit()

    def _activate_plpythonu(self):
        """As from link http://stackoverflow.com/questions/18209625/how-do-i-modify-fields-inside-the-new-postgresql-json-datatype"""

        self._execute("CREATE EXTENSION IF NOT EXISTS plpythonu;")
        self._commit()
        self._execute("CREATE LANGUAGE plpythonu;")
        self._commit()

    def _json_update(self):

        self._execute("""CREATE OR REPLACE FUNCTION json_update(data json, key text, value text)
         RETURNS json
         AS $$
            import json
            json_data = json.loads(data)
            json_data[key] = value
            return json.dumps(json_data, indent=4)
         $$ LANGUAGE plpythonu;""")
        self._commit()

    def init_store(self):
        """
        Runs on server with super user privileges
        """
        if self.schema:
            # User
            try:
                self._execute("CREATE USER %s WITH PASSWORD '%s'" % (self.schema,
                    self.password))
            except Exception, e:
                self.session.rollback()
                if "already exists" in repr(e):
                    logger.info("Could not create user '%s', already exists." % self.schema)
                    logger.info("Update password anyway for user '%s'" % self.schema)
                    self._execute("ALTER USER %s WITH PASSWORD '%s'" % (self.schema, self.password))
                else:
                    logger.exception("Could not create user '%s'." % self.schema)

            # Schema
            try:
                self.engine.execute(CreateSchema(self.schema))
                logger.info("Schema created")
            except Exception, e:
                self.session.rollback()
                if "already exists" in repr(e):
                    logger.info("Could not create schema '%s', already exists." % self.schema)
                else:
                    logger.exception("Could not create schema '%s'." % self.schema)

            # Permissions
            self._execute("GRANT USAGE ON SCHEMA %s to %s;" % (self.schema, self.schema))
            self._execute("GRANT ALL ON ALL TABLES IN  SCHEMA %s to %s;" % (self.schema, self.schema))
            self._execute("GRANT ALL ON ALL SEQUENCES IN  SCHEMA %s to %s;" % (self.schema, self.schema))
            self._commit()
        else:
            logger.warn("No schema specified")
        self._prepare()
        return "init_store '%s' done" % self.schema

    def _prepare(self):
        Base.metadata.create_all(self.engine)
        self._commit()

    def write_obj(self, obj):
        self.session.add(obj)
        self._commit()

    def write_dict(self, data_dict):
        obj_dict = DataObject(data=data_dict)
        return self.write_obj(obj_dict)

    def _commit(self):
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise

    def update(self, obj):
        flag_modified(obj, "data")
        self._commit()

    def all(self, lock=False, nowait=False, read=False, skip_locked=False):
        if lock:
            self.session.autocommit = False
            #self.session.begin()
            try:
                return self.session.query(DataObject).with_for_update(nowait=nowait, skip_locked=skip_locked, read=read).all()
            except Exception, e:
                logger.error(e)
                if "could not obtain lock on row" in repr(e):
                    self.session.rollback()
                    raise LockException(e)
                raise e
        else:
            return self.session.query(DataObject).all()

    def count(self):
        return self.session.query(DataObject).count()

    def filter(self, k, v, lock=False, nowait=True, skip_locked=False, read=False):
        if lock:
            try:
                qs = self.session.query(DataObject).filter(text("data->>'"+k+"' = '"+v+"'")).with_for_update(nowait=nowait, skip_locked=skip_locked, read=read).all()
            except Exception, e:
                logger.error(e)
                if "could not obtain lock on row" in repr(e):
                    self.session.rollback()
                    raise LockException(e)
                raise e
        else:
            qs = self.session.query(DataObject).filter(text("data->>'"+k+"' = '"+v+"'")).with_for_update(read=read).all()

        return qs

    def delete(self, obj):
        self.session.delete(obj)
        return self._commit()

    def save(self, obj):
        return self._commit()

    def get(self, k, v, lock=False, nowait=False):
        if lock:
            result = self.filter(k, v, lock, nowait)
        else:
            result = self.filter(k, v)
        if len(result) > 1:
            raise Exception("More than one row returned! (%s)" % len(result))
        elif len(result) < 1:
            return None
        return result[0]

    def _execute(self, sql, commit=True, result=None):
        logger.info(sql)
        result = self.session.execute(sql)
        if commit:
            self._commit()
        return result

    def truncate(self):
        self._execute("TRUNCATE %s.data_table" % self.schema)


def resultproxy_to_list(proxy):
    l = []
    for row in proxy:
        l.append(row.__dict__)
    return l


class PsqlDataStore(DataStore):
    __metaclass__ = Singleton

    ENGINE = 'postgresql+psycopg2://%(USER)s:%(PASSWORD)s@%(HOST)s:%(PORT)s/%(NAME)s'

    def query(self, k, v):
        q = """SELECT id, json_string(data,'%s'
                FROM things
                WHERE json_string(data,'%s')
                LIKE '%s%';""" % (k, v)


class PsqlDataStoreSingleton(PsqlDataStore):
    __metaclass__ = Singleton


@register_plugin
class DataStorePlugin(Plugin):

    def attach_worker(self, **kwargs):
        logger.info("Attach to worker")
        return PsqlDataStoreSingleton(schema=kwargs['USER'],
                                      password=kwargs['PASSWORD'], **kwargs)

    @classmethod
    def init(cls):
        logger.info("Init %s" % cls)
        plugin_path = os.path.dirname(inspect.getfile(cls))
        template_path = os.path.join(plugin_path, "templates")
        settings.TEMPLATE_DIRS = settings.TEMPLATE_DIRS + (template_path,)

    def config(self, base):
        plugin_settings = settings.TUMBO_PLUGINS_CONFIG['core.plugins.datastore']
        plugin_settings['USER'] = base.name.replace("-", "_")
        plugin_settings['PASSWORD'] = base.executor.password
        return plugin_settings

    def on_start_base(self, base):
        plugin_settings = settings.TUMBO_PLUGINS_CONFIG['core.plugins.datastore']
        store = PsqlDataStore(schema=base.name, password=base.executor.password,
                              keep=False, **plugin_settings)
        return store.init_store()

    def cockpit_context(self):
        plugin_settings = settings.TUMBO_PLUGINS_CONFIG['core.plugins.datastore']
        SCHEMAS = "SELECT schema_name FROM information_schema.schemata;"
        TABLESPACES = """SELECT array_to_json(array_agg(row_to_json(t))) FROM (
                SELECT *, pg_tablespace_size(spcname) FROM pg_tablespace
            ) t;"""
        CONNECTIONS = "SELECT * FROM pg_stat_activity;"
        CONNECTIONS_COUNT = "SELECT count(*) FROM pg_stat_activity;"
        LOCKS = "SELECT query,state,waiting,pid FROM pg_stat_activity WHERE datname='store' AND NOT (state='idle' OR pid=pg_backend_pid());"

        return {
            'SCHEMAS': [row for row in PsqlDataStore(keep=False, **plugin_settings)._execute(SCHEMAS, commit=False)],
            'TABLESPACES': [row for row in PsqlDataStore(keep=False, **plugin_settings)._execute(TABLESPACES, commit=False)][0],
            'CONNECTIONS': [row for row in PsqlDataStore(keep=False, **plugin_settings)._execute(CONNECTIONS, commit=False)],
            'CONNECTIONS_COUNT': [row for row in PsqlDataStore(keep=False, **plugin_settings)._execute(CONNECTIONS_COUNT, commit=False)],
            'LOCKS': [row for row in PsqlDataStore(keep=False, **plugin_settings)._execute(LOCKS, commit=False)]
        }
        return {}

class LockException(Exception):
    pass
