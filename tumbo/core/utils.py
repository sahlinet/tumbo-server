import datetime
import logging
import dropbox
import json
import StringIO
import hashlib
import pika
import os
import re
from django.contrib import messages
from django.conf import settings
from dropbox.rest import ErrorResponse
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth import get_user_model

from core.queue import connect_to_queue
from core import defaults

import sys
import _ast
from pyflakes import checker
from pyflakes import reporter as modReporter
from pyflakes.messages import Message

from django.core.urlresolvers import reverse
from django.test import RequestFactory

class UnAuthorized(Exception):
    pass

class NotFound(Exception):
    pass

class NoBasesFound(Exception):
    pass

logger = logging.getLogger(__name__)


class Connection(object):

    def __init__(self, access_token):
        self.client = dropbox.client.DropboxClient(access_token)
        super(Connection, self).__init__()

    def info(self):
        account_info = self.client.account_info()
        email = account_info['email']
        name = account_info['display_name']
        return email, name

    def listing(self):
        bases = []
        for base in self._call('metadata', '/')['contents']:
            bases.append(base['path'].lstrip('/'))
        if len(bases) == 0:
            raise NoBasesFound()
        return bases

    def get_file(self, path):
        logger.debug("get file %s" % path)
        return self._call('get_file', path)

    def get_file_content_and_rev(self, path):
        file, metadata = self._call('get_file_and_metadata', path)
        content = file.read()
        file.close()
        rev = metadata['rev']
        return content, rev

    def get_file_content(self, path):
        logger.debug("return content %s" % path)
        return self.get_file(path).read()

    def put_file(self, path, content):
        f = StringIO.StringIO(content)
        return self._call('put_file', path, f, True)

    def delete_file(self, path):
        return self._call('file_delete', path)

    def create_folder(self, path):
        return self._call('file_create_folder', path)

    def delta(self, cursor):
        return self._call('delta', cursor)

    def _call(self, ms, *args):
        try:
            m = getattr(self.client, ms)
            return m(*args)
        except ErrorResponse, e:
            if e.__dict__['status'] == 401:
                raise UnAuthorized(e.__dict__['body']['error'])
            if e.__dict__['status'] == 404:
                raise NotFound(e.__dict__['body']['error'])
            raise e
        except Exception, e:
            raise e

    def metadata(self, path):
        return self._call('metadata', path)

    def directory_zip(self, path, zf):

        logger.info("download "+path)
        try:
            f_metadata = self.metadata(path)

            if f_metadata['is_dir']:
                for content in f_metadata['contents']:
                    logger.info("download "+content['path'])

                    if content['is_dir'] == True:
                        self.directory_zip(content['path'], zf)
                    else:
                        # get the file
                        filepath = content['path']
                        try:
                            file = self.get_file(filepath)
                            filepath = re.sub(r"(.+?)(\/.*)", r"\2", filepath)
                            zf.writestr(os.path.relpath(filepath, "/"), file.read())
                            file.close()
                        except ErrorResponse, e:
                            logger.error(e)

        except ErrorResponse, e:
            logger.error(e)

        return zf


def message(request, level, message):
    dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if level == logging.ERROR:
        tag = "alert-danger"
    elif level == logging.INFO:
        tag = "alert-info"
    elif level == logging.WARN:
        tag = "alert-info"
    messages.error(request, dt + " " + str(message)[:1000], extra_tags="%s safe" % tag)


def sign(data):
    m = hashlib.md5()
    m.update(data)
    m.update(settings.SECRET_KEY)
    return "%s-%s" % (data, m.hexdigest()[:10])


def channel_name_for_user(request):
    if request.user.is_authenticated():
        channel_name = "%s-%s" % (request.user.username, sign(request.user.username))
    else:
        #channel_name = "anon-%s" % sign(request.session.session_key)
        # TODO: find a way to identify anonymous user
        #     problem on initial
        channel_name = "anon-%s" % sign(request.META['REMOTE_ADDR'])
    logger.debug("channel_name: %s" % channel_name)
    return channel_name


def channel_name_for_user_by_user(user):
    channel_name = "%s-%s" % (user.username, sign(user.username))
    logger.debug("channel_name: %s" % channel_name)
    return channel_name


def send_client(channel_name, event, data):
    return
    logger.debug("START EVENT_TO_QUEUE %s"   % event)

    host = settings.RABBITMQ_HOST
    port = int(settings.RABBITMQ_PORT)
    user = getattr(settings, "RABBITMQ_ADMIN_USER", "guest")
    password = getattr(settings, "RABBITMQ_ADMIN_PASSWORD", "guest")

    #channel = pusher
    channel = connect_to_queue(host, 'pusher_events', "/", username=user, password=password, port=port)
    payload = {
        'channel': channel_name,
        'event': event,
        'data': data,
    }

    channel.basic_publish(exchange='',
                          routing_key='pusher_events',
                          body=json.dumps(payload),
                          properties=pika.BasicProperties(
                            delivery_mode=1,
                         ),
                        )
    logger.debug("END EVENT_TO_QUEUE %s" % event)
    channel.close()
    channel.connection.close()
    del channel.connection
    del channel

def user_message(level, channel_name, message):

    #channel = username
    # TODO: strip message to max 10KB
    # http://pusher.com/docs/server_api_guide/server_publishing_events

    #p = get_pusher()

    now = datetime.datetime.now()
    if level == logging.INFO:
        class_level = "info"
    elif level == logging.DEBUG:
        class_level = "debug"
    elif level == logging.WARNING:
        class_level = "warn"
    elif level == logging.ERROR:
        class_level = "error"
    #logger.log(level, "to pusher: "+message)
    data = {'datetime': str(now), 'message': str(message), 'class': class_level}
    send_client(channel_name, "console_msg", data)


def info(username, gmessage):
        return user_message(logging.INFO, username, gmessage)
def debug(username, gmessage):
        return user_message(logging.DEBUG, username, gmessage)
def error(username, gmessage):
        return user_message(logging.ERROR, username, gmessage)
def warn(username, gmessage):
        return user_message(logging.WARN, username, gmessage)


def check_code(code, name):
    errors = []

    class CustomMessage(object):
        pass

    reporter = modReporter._makeDefaultReporter()
    try:
        tree = compile(code, name, "exec", _ast.PyCF_ONLY_AST)
    except SyntaxError:
        value = sys.exc_info()[1]
        msg = value.args[0]

        (lineno, offset, text) = value.lineno, value.offset, value.text

        # If there's an encoding problem with the file, the text is None.
        if text is None:
            # Avoid using msg, since for the only known case, it contains a
            # bogus message that claims the encoding the file declared was
            # unknown.
            reporter.unexpectedError(name, 'problem decoding source')
        else:
            reporter.syntaxError(name, msg, lineno, offset, text)

        loc = CustomMessage()
        loc.lineno = lineno
        loc.offset = offset
        msg = Message(name, loc)
        msg.message = "SyntaxError"
        errors.append(msg)
    except Exception, e:
        loc = CustomMessage()
        loc.lineno = lineno
        loc.offset = offset
        msg = Message(name, loc)
        msg.message = "Problem decoding source"
        errors.append(msg)

        reporter.unexpectedError(name, 'problem decoding source')
        logger.error("problem decoding source")
        logger.exception()

    #if len(errors) > 0:
    #    return errors

    r = []
    try:
        w = checker.Checker(tree, name)
        r = w.messages
        for message in w.messages:
            logger.info(str(message))
        #    r.append(str(message).split(":"))
    except UnboundLocalError, e:
        pass
    return not (len(r) > 0 or len(errors) > 0), r, errors


def load_setting(name, fail=True):
    v=None
    default = getattr(defaults, name, None)
    setting = getattr(settings, name, None)
    if setting:
        v = setting
        logger.debug("Loaded setting from settings %s with value: %s" % (name, v))
    elif default:
        v = default
        logger.debug("Loaded setting from defaults %s with value: %s" % (name, v))
    if not v and fail:
        logger.error("Could not load setting %s" % name)
        raise ImproperlyConfigured(name)
    return v


def load_var_to_file(var):
    path = "/tmp/"
    fq_file = os.path.join(path, var)
    content = os.environ[var]
    if not os.path.exists(path):
        os.mkdir(path)
    if not os.path.exists(fq_file):
        f = open(fq_file, 'w')
        f.write(content)
        f.close()
        if sys.platform == "darwin":
            os.popen4("echo $(cat %s) > %s" % (fq_file, fq_file))
        else:
            os.popen4("echo -e $(cat %s) > %s" % (fq_file, fq_file))
    return fq_file


def call_apy(base_name, apy_name):
    logger.info("START call_apy")
    try:
        from core.models import Apy
        apy = Apy.objects.get(name=apy_name, base__name=base_name)
        logger.info("START call_apy %s" % apy.name)
        url = reverse('exec', kwargs={'base': apy.base.name, 'id': apy.id})

        request_factory = RequestFactory()
        request = request_factory.get(url, data={'json': "", 'base': apy.base.name,
                                                 'id': apy.id})
        # TODO: fails if user admin is not created
        request.user = get_user_model().objects.get(username='admin')
        request.META['HTTP_ACCEPT'] = "text/html"

        from core.views import DjendExecView
        view = DjendExecView()
        response = view.get(request, base=apy.base.name, id=apy.id)
        logger.info("method called for base %s, response_code: %s" % (apy.base.name, response.status_code))
        logger.info("END call_apy %s" % apy.name)
    except Exception, e:
        logger.error("ERROR call_apy")
        logger.exception(e)

import cProfile
def profileit(func):
    """
    Taken from http://stackoverflow.com/questions/5375624/a-decorator-that-profiles-a-method-call-and-logs-the-profiling-result
    """
    def wrapper(*args, **kwargs):
        prof = cProfile.Profile()
        #if not os.environ.has_key("PROFILE_DO_FUNC"):
        #    return func(*args, **kwargs)
        retval = prof.runcall(func, *args, **kwargs)
		# Note use of name from outer scope
		#prof.dump_stats(name)
        import pstats
        s = pstats.Stats(prof).sort_stats('time')
        s.print_stats(8)
        return retval
    return wrapper


def totimestamp(t):
    logger.debug("totimestamp: %s" % t)
    return (t-datetime.datetime(1970, 1, 1)).total_seconds()


def fromtimestamp(t):
    logger.info("fromtimestamp: %s" % t)
    return datetime.datetime.fromtimestamp(t)
