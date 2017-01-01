import pika
import uuid
import os
import json
import copy
import logging
import sys
import traceback
import base64

from bunch import Bunch

from django.conf import settings

from core.queue import connect_to_queuemanager, CommunicationThread
from core.queue import connect_to_queue
from core.utils import load_setting, read_jwt, check_code
from core.plugins import PluginRegistry
from core import responses


logger = logging.getLogger(__name__)

RESPONSE_TIMEOUT = 30
STATIC_RESPONSE_TIMEOUT = 5
CONFIGURATION_QUEUE = "configuration"
CONFIGURATION_EVENT = CONFIGURATION_QUEUE
FOREIGN_CONFIGURATION_QUEUE = "fconfiguration"
FOREIGN_CONFIGURATION_EVENT = CONFIGURATION_QUEUE

SETTINGS_EVENT = "setting"
SETTING_QUEUE = SETTINGS_EVENT

PLUGIN_CONFIG_QUEUE = "pluginconfig"

RPC_QUEUE = "rpc_queue"
STATIC_QUEUE = "static_queue"


class Worker():

    def start(self):
        pass

    def stop(self):
        pass

    def is_running(self):
        pass

    def running(self):
        pass

    def update(self):
        pass

    def execute(self):
        pass


def distribute(event, body, vhost, username, password):
    logger.debug("distribute called")

    class ExecutorClient(object):
        """
        Gets the apy (id, name, module) and sets them on the _do function.__add__ .
        Then the client is ready to response for execution requests.

        """
        def __init__(self, vhost, event, username, password):
            # get needed stuff
            self.vhost = vhost
            self.event = event
            self.username = username
            self.password = password
            logger.debug("exchanging message to vhost : %s" % self.vhost)
            logger.debug("exchanging message to vhost username: %s" % self.username)
            self.connection = connect_to_queuemanager(
                host=settings.RABBITMQ_HOST,
                vhost=vhost,
                username=username,
                password=password,
                port=int(settings.RABBITMQ_PORT),
            )

            self.channel = self.connection.channel()
            self.channel.exchange_declare(exchange=CONFIGURATION_QUEUE, type='fanout')
            self.channel.exchange_declare(exchange=FOREIGN_CONFIGURATION_QUEUE, type='fanout')


        def call(self, body):
            self.channel.basic_publish(
                exchange=CONFIGURATION_QUEUE,
                routing_key='',
                body=body,
                properties=pika.BasicProperties(app_id=event)
            )

            self.connection.close()

    executor = ExecutorClient(vhost, event, username, password)
    executor.call(body)

    return True


def call_rpc_client(apy, vhost, username, password, async=False):

    class ExecutorClient(object):
        """
        Gets the apy (id, name, module) and sets them on
        the _do function.__add__ .
        Then the client is ready to response for execution requests.

        """
        def __init__(self, vhost, username, password, async=False):
            # get needed stuff
            self.vhost = vhost
            self.connection = connect_to_queuemanager(
                host=settings.RABBITMQ_HOST,
                vhost=vhost,
                username=username,
                password=password,
                port=settings.RABBITMQ_PORT
            )

            logger.debug("exchanging message to vhost: %s" % self.vhost)

            self.channel = self.connection.channel()

            self.async = async

            self._set_callback_queue()


        def _set_callback_queue(self):

            if not self.async:
                result = self.channel.queue_declare(exclusive=True)
                self.callback_queue = result.method.queue
            else:
                self.callback_queue = "async_callback"
                result = self.channel.queue_declare(queue=self.callback_queue)

            self.channel.basic_consume(self.on_response, no_ack=True,
                                       queue=self.callback_queue)

        def on_timeout(self):
            logger.error("timeout in waiting for response")
            raise Exception("Timeout")

        def on_response(self, ch, method, props, body):
            if self.corr_id == props.correlation_id:
                self.response = body
                logger.debug("from rpc queue: "+body)

        def call(self, n):
            if not self.async:
                self.connection.add_timeout(RESPONSE_TIMEOUT, self.on_timeout)
            self.response = None
            self.corr_id = str(uuid.uuid4())
            expire = 5000
            logger.debug("Message expiration set to %s ms" % str(expire))
            properties = pika.BasicProperties(
                reply_to=self.callback_queue,
                delivery_mode=1,
                correlation_id=self.corr_id,
                expiration=str(expire)
            )
            self.channel.basic_publish(exchange='',
                                       routing_key=RPC_QUEUE,
                                       properties=properties,
                                       body=str(n))
            logger.info("Message published to: %s:%s" %
                        (self.vhost, RPC_QUEUE))
            while self.response is None and not self.async:
                self.connection.process_data_events()
            return self.response

        def end(self):
            self.channel.close()
            self.connection.close()
            del self.channel
            del self.connection

    if not async:
        executor = ExecutorClient(vhost, username, password)
    else:
        executor = ExecutorClient(
            vhost,
            load_setting("CORE_RECEIVER_USERNAME"),
            load_setting("TUMBO_CORE_RECEIVER_PASSWORD"),
            async=async
            )

    try:
        response = executor.call(apy)
    except Exception, e:
        logger.warn(e)
        response = json.dumps(
            {u'status': u'TIMEOUT',
                u'exception': None,
                u'returned': None,
                'id': u'cannot_import'})
    finally:
        executor.end()
    return response


STATE_OK = "OK"
STATE_NOK = "NOK"
STATE_NOT_FOUND = "NOT_FOUND"

threads = []


class ExecutorServerThread(CommunicationThread):

    def __init__(self, *args, **kwargs ):
        self.functions = {}
        self.foreign_functions = {}
        self.settings = {}
        self.pluginconfig = {}

        super(ExecutorServerThread, self).__init__(*args, **kwargs)

    @property
    def state(self):
        return {'name': self.name,
                'count_settings': len(self.settings),
                'count_functions': len(self.functions),
                'settings': self.settings.keys(),
                'functions': self.functions.keys(),
                'connected': self.is_connected
                }

    def on_message(self, ch, method, props, body):
        try:
            if method.exchange == "configuration":
                if props.app_id == "configuration":
                    fields = json.loads(body)[0]['fields']
                    try:
                        ok, warnings, errors = check_code(fields['module'], fields['name'])
                        exec fields['module'] in globals(), locals()
                        if ok:
                            self.functions.update({
                                fields['name']: func,
                                })
                            logger.info("Configuration '%s' received in %s" % (fields['name'], self.name))
                        else:
                            logger.error("Configuration '%s' failed in %s" % (fields['name'], self.name))
                            logger.error(warnings, errors)
                    except Exception, e:
                        traceback.print_exc()
                elif props.app_id == "fconfiguration":
                    fields = json.loads(body)[0]['fields']
                    try:
                        exec fields['module'] in globals(), locals()
                        self.foreign_functions.update({
                            fields['name']: func,
                            })
                        logger.info("Configuration '%s' received in %s" % (fields['name'], self.name))
                    except Exception, e:
                        traceback.print_exc()

                elif props.app_id == "setting":
                    json_body = json.loads(body)
                    key = json_body.keys()[0]
                    self.settings.update(json_body)
                    logger.info("Setting '%s' received in %s" % (key, self.name))

                elif props.app_id == PLUGIN_CONFIG_QUEUE:
                    json_body = json.loads(body)
                    logger.info("Pluginconfig (%s) received and attached to self.pluginconfig" % str(json_body.keys()))
                    self.pluginconfig.update(json_body)
                else:
                    logger.error("Invalid event arrived (%s)" % props.app_id)

            if method.routing_key == RPC_QUEUE:

                #import gc
                #import objgraph
                #gc.collect()
                #objgraph.show_most_common_types(limit=10)
                #objgraph.show_growth()

                logger.info("Request received in %s (%s)" % (self.name, str(props.reply_to)))
                try:
                    response_data = {}
                    response_data = _do(json.loads(body), self.functions, self.foreign_functions, self.settings, self.pluginconfig)
                    logger.debug("RECEIVED: %s" % str(response_data))
                except Exception, e:
                    logger.exception(e)
                finally:
                    if props.reply_to == "async_callback":
                        # TODO: should be a user with less permissions
                        connection = connect_to_queuemanager(
                                self.host,
                                load_setting("CORE_VHOST"),
                                load_setting("CORE_SENDER_USERNAME"),
                                load_setting("TUMBO_CORE_SENDER_PASSWORD"),
                                self.port
                                )
                        channel = connection.channel()
                        response_data.update({'rid': json.loads(body)['rid']})
                        channel.basic_publish(exchange='',
                                              routing_key="async_callback",
                                              body=json.dumps(response_data)
                                              )
                        connection.close()

                    else:
                        try:
                            response_data_json = json.dumps(response_data)
                        except Exception, e:
                            logger.exception(e)
                            exception = "%s" % type(e).__name__
                            exception_message = repr(e)
                            #trc = traceback.format_exc()
                            status = STATE_NOK
                            response_data_json = json.dumps({
                                "status": status,
                                "returned": None,
                                "exception": exception,
                                "exception_message": exception_message,
                                "response_class": None
                                })
                        ch.basic_publish(exchange='',
                                         routing_key=props.reply_to,
                                         properties=pika.BasicProperties(
                                            correlation_id=props.correlation_id,
                                            delivery_mode=1,
                                            ),
                                         body=response_data_json)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.debug("Response sent %s (%s)" % (self.name,
                                                       str(props.reply_to)))
        except Exception, e:
            logger.exception(e)


class ApyNotFound(Exception):
    pass


class ApyError(Exception):
    pass


def log_to_queue(tid, level, msg):
    host = settings.RABBITMQ_HOST
    port = settings.RABBITMQ_PORT
    vhost = load_setting("CORE_VHOST")
    username = load_setting("CORE_SENDER_USERNAME")
    password = load_setting("TUMBO_CORE_SENDER_PASSWORD")
    log_queue_name = load_setting("LOGS_QUEUE")

    channel = connect_to_queue(host, log_queue_name, vhost,
                               username=username, password=password, port=port)

    payload = {
        'rid': tid,
        'level': level,
        'msg': msg,
    }

    channel.basic_publish(exchange='',
                          routing_key=log_queue_name,
                          body=json.dumps(payload),
                          properties=pika.BasicProperties(
                              delivery_mode=1,
                          ))
    channel.close()
    channel.connection.close()
    del channel.connection
    del channel


def info(tid, msg):
    log_to_queue(tid, logging.INFO, msg)


def warning(tid, msg):
    log_to_queue(tid, logging.WARNING, msg)


def debug(tid, msg):
    log_to_queue(tid, logging.DEBUG, msg)


def error(tid, msg):
    log_to_queue(tid, logging.ERROR, msg)


def _do(data, functions=None, foreign_functions=None, settings=None, pluginconfig={}):
        exception = None
        exception_message = None
        returned = None
        status = STATE_OK

        logger.info("DATA: "+str(data))

        request = Bunch(data['request'])
        base_name = data['base_name']
        model = json.loads(data['model'])

        response_class = None


        # worker does not know apy
        if model['fields']['name'] not in functions:
            status = STATE_NOT_FOUND
            logger.warn("method %s not found in functions, known: %s" %
                        (model['fields']['name'], str(functions.keys())))
        # go ahead
        else:
            func = functions[model['fields']['name']]
            logger.debug("do %s" % request)

            logger.debug("START DO")
            try:

                token, payload = read_jwt(request['token'], os.environ.get('secret'))
                del payload['expiry']
                del request['token']

                func.identity = payload
                func.request = request

                func.rid = data['rid']

                func.name = model['fields']['name']

                # attach GET and POST data
                func.method = copy.deepcopy(request['method'])
                func.GET = copy.deepcopy(request['GET'])
                func.POST = copy.deepcopy(request['POST'])

                # attach Responses classes
                func.responses = responses

                # attach log functions
                func.info = info
                func.debug = debug
                func.warn = warning
                func.error = error

                # attatch settings
                setting_dict = settings
                setting_dict1 = Bunch()
                for key, value in setting_dict.iteritems():
                    setting_dict1.update({key: value})
                setting_dict1.update({'STATIC_DIR': "/%s/%s/static" %
                                     ("fastapp", base_name)})
                func.settings = setting_dict1

                # attach foreign_functions
                func.foreigns = Bunch(foreign_functions)

                # attach siblings
                func.siblings = Bunch(functions)

                if model['fields']['name'] != "init":
                    # attach plugins
                    plugins = PluginRegistry()
                    for plugin in plugins.all_plugins:
                        try:
                            logger.info("%s: Attach with settings: %s" % (plugin.name, pluginconfig[plugin.name].keys()))
                            setattr(func, plugin.shortname, plugin.attach_worker(**pluginconfig[plugin.name]))
                            if not hasattr(func, plugin.shortname):
                                logger.warning("Func is None")
                            logger.info("%s: Func attached to _do" % plugin.shortname)
                        except Exception, e:
                            logger.exception("%s: Not able to attach, pluginconfig is: %s" % (plugin, pluginconfig))

                # execution
                returned = func(func)
                logger.info("Returned is of type: %s" % type(returned))
                if isinstance(returned, responses.Response):
                    # serialize
                    response_class = returned.__class__.__name__
                    returned = str(returned)
                    #returned = returned

            except Exception, e:
                logger.exception(e)
                exception = "%s" % type(e).__name__
                exception_message = repr(e)
                status = STATE_NOK

                # log to user
                trc = traceback.format_exc()
                error(data['rid'], repr(e) + ": " + trc)

            logger.debug("END DO")
        return_data = {"status": status, "returned": returned,
                       "exception": exception,
                       "exception_message": exception_message, "response_class": response_class}
        if exception_message:
            return_data['exception_message'] = exception_message
        return return_data


def get_static(path, vhost, username, password, async=False):

    class StaticClient(object):
        """
        Gets the apy (id, name, module) and sets them on the _do function.__add__ .
        Then the client is ready to response for execution requests.

        """
        def __init__(self, vhost, username, password, async=False):
            # get needed stuff
            self.vhost = vhost
            self.connection = connect_to_queuemanager(
                host=settings.RABBITMQ_HOST,
                vhost=vhost,
                username=username,
                password=password,
                port=settings.RABBITMQ_PORT
                )

            logger.debug("exchanging message to vhost: %s" % self.vhost)

            self.channel = self.connection.channel()

            result = self.channel.queue_declare(exclusive=True)

            self.callback_queue = result.method.queue
            self.channel.basic_consume(self.on_response, no_ack=True,
                                       queue=self.callback_queue)

        def on_timeout(self):
            logger.error("timeout in waiting for response")
            raise Exception("Timeout")

        def on_response(self, ch, method, props, body):
            logger.debug("StaticClient.on_message")
            if self.corr_id == props.correlation_id:
                self.response = body
                logger.debug("from static queue: "+body[:100])
            else:
                logger.warn("correlation_id did not match (%s!=%s)" %
                            (self.corr_id, props.correlation_id))

        def call(self, n):
            if self.callback_queue != "/static_callback":
                async = False
                self.connection.add_timeout(3, self.on_timeout)
                #self.connection.add_timeout(RESPONSE_TIMEOUT, self.on_timeout)
            self.response = None
            self.corr_id = str(uuid.uuid4())
            expire = 10000
            logger.debug("Message expiration set to %s ms" % str(expire))
            logger.debug("Wait for corr_id %s" % self.corr_id)
            self.channel.basic_publish(exchange='',
                                       routing_key=STATIC_QUEUE,
                                       properties=pika.BasicProperties(
                                           reply_to=self.callback_queue,
                                           delivery_mode=1,
                                           correlation_id=self.corr_id,
                                           expiration=str(expire)
                                           ),
                                       body=str(n))
            while self.response is None and not async:
                self.connection.process_data_events()
            return self.response

        def end(self):
            self.channel.close()
            self.connection.close()
            del self.channel
            del self.connection

    executor = StaticClient(vhost, username, password, async=async)

    try:
        response = executor.call(path)
    except Exception, e:
        logger.exception(e)
        response = json.dumps({u'status': u'TIMEOUT', u'exception': None,
                               u'returned': None, 'id': u'cannot_import'})
    finally:
        executor.end()
    return response


class StaticServerThread(CommunicationThread):

    def __init__(self, *args, **kwargs):
        return super(StaticServerThread, self).__init__(*args, **kwargs)

    def on_message(self, ch, method, props, body):
        logger.debug(self.name+": "+sys._getframe().f_code.co_name)
        logger.debug(body)
        body = json.loads(body)

        rc = None

        try:
            # logger.debug(method.routing_key)
            if method.routing_key == STATIC_QUEUE:
                logger.debug("Static-Request %s received in %s" % (body['path'], self.name))
                try:
                    path = body['path']
                    response_data = {}
                    base_name = body['base_name']
                    f = None
                    full_path = None
                    for p in sys.path:
                        logger.debug("Checking in path '%s'" % p)
                        if base_name in p:
                            logger.debug(p+" found")
                            full_path = os.path.join(p,
                                         path.replace(base_name+"/", "")
                                         )
                            logger.debug("%s:  found" % full_path)
                            try:
                                f = open(full_path, 'r')
                                last_modified = os.stat(full_path).st_mtime
                                rc = "OK"
                                response_data.update({
                                    'file': base64.b64encode(f.read()),
                                    'LM': last_modified
                                    })
                            except Exception, e:
                                logger.warning("Could not open file %s" % full_path)
                                rc = "ERROR"
                            finally:
                                break
                                if f:
                                    f.close()
                    if not f:
                        #logger.warning("%s not found" % full_path)
                        rc = "NOT_FOUND"

                except Exception, e:
                    rc = "NOT_FOUND"
                    logger.exception(e)
                finally:
                    response_data.update({'status': rc})
                    publish_result = ch.basic_publish(exchange='',
                                     routing_key=props.reply_to,
                                     properties=pika.BasicProperties(
                                        correlation_id=props.correlation_id,
                                        delivery_mode=1,
                                        ),
                                     body=json.dumps(response_data))
                    logger.debug("message published: %s" % str(publish_result))
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    logger.debug("Static-Request %s response in %s (%s)" % (body['path'], self.name, rc))
        except Exception, e:
            logger.exception(e)
