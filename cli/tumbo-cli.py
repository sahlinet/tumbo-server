#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Tumbo

Usage:
  tumbo-cli.py server dev run [--ngrok-hostname=host] [--ngrok-authtoken=token] [--autostart] [--coverage]
  tumbo-cli.py server docker run [--stop-after=<seconds>] [--ngrok-hostname=host] [--ngrok-authtoken=token]
  tumbo-cli.py server docker stop
  tumbo-cli.py server docker build
  tumbo-cli.py server docker pull
  tumbo-cli.py server docker url
  tumbo-cli.py server docker logs
  tumbo-cli.py env list
  tumbo-cli.py env <env-id> login <url>
  tumbo-cli.py env <env-id> logout
  tumbo-cli.py env <env-id> active
  tumbo-cli.py env <env-id> open
  tumbo-cli.py project list [--env=<env>]
  tumbo-cli.py project <base-name> show [--env=<env>]
  tumbo-cli.py project <base-name> open [--env=<env>]
  tumbo-cli.py project <base-name> start [--env=<env>]
  tumbo-cli.py project <base-name> stop [--env=<env>]
  tumbo-cli.py project <base-name> restart [--env=<env>]
  tumbo-cli.py project <base-name> destroy [--env=<env>]
  tumbo-cli.py project <base-name> delete [--env=<env>]
  tumbo-cli.py project <base-name> create [--env=<env>]
  tumbo-cli.py project <base-name> function <function-name> execute [--async] [--public] [--nocolor] [--env=<env>]
  tumbo-cli.py project <base-name> function <function-name> create [--env=<env>]
  tumbo-cli.py project <base-name> function <function-name> edit [--env=<env>]
  tumbo-cli.py project <base-name> transactions [--tid=<tid>]  [--logs] [--cut=<cut>] [--nocolor] [--env=<env>]

  # tumbo-cli.py project <base-name> export [filename] [--env=<env>]
   tumbo-cli.py project <base-name> import <zipfile> [--env=<env>]

  # tumbo-cli.py server dev test
  # tumbo-cli.py server docker test
  # tumbo-cli.py project <base-name> function <function-name> show [--env=<env>]
  # tumbo-cli.py project <base-name> transport <env> [--env=<env>]
  # tumbo-cli.py project <name> settings edit
  # tumbo-cli.py project <name> datastore <show>
  # tumbo-cli.py --version

Options:
  -h --help         Show this screen.
  --version         Show version.
  --env=env         Use different environment than active.
  --cut=cut         Cut output after n character.
"""
import sys
import os
import sh
import time
import signal
import requests
import getpass
import json
import pprint
import logging
import tempfile

from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import Terminal256Formatter

from docopt import docopt
from tabulate import tabulate

docker_compose = sh.Command("docker-compose")
bash = sh.Command("bash")
python = sh.Command(sys.executable)

coverage_cmd = "coverage run --timid --source=tumbo --parallel-mode "

try:
    import tumbo
    tumbo_path = os.path.join(os.path.dirname(tumbo.__file__), "..")
    manage_py = "%s/tumbo/manage.py" % tumbo_path
    compose_files_path = sys.prefix+"/tumbo_server/compose-files"
except ImportError:
    tumbo_path = os.path.abspath(".")
    manage_py = "tumbo/manage.py"
    compose_files_path = "compose-files"

compose_file = "%s/docker-compose-app-docker_socket_exec.yml" % compose_files_path
compose_file_base = "%s/docker-compose-base.yml" % compose_files_path

def confirm(prompt=None, resp=False):
    """prompts for yes or no response from the user. Returns True for yes and
    False for no.

    'resp' should be set to the default value assumed by the caller when
    user simply types ENTER.

    >>> confirm(prompt='Create Directory?', resp=True)
    Create Directory? [y]|n: 
    True
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y: 
    False
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y: y
    True

    """
    
    if prompt is None:
        prompt = 'Confirm'

    if resp:
        prompt = '%s [%s]|%s: ' % (prompt, 'y', 'n')
    else:
        prompt = '%s [%s]|%s: ' % (prompt, 'n', 'y')
        
    while True:
        ans = raw_input(prompt)
        if not ans:
            return resp
        if ans not in ['y', 'Y', 'n', 'N']:
            print('please enter y or n.')
            continue
        if ans == 'y' or ans == 'Y':
            return True
        if ans == 'n' or ans == 'N':
            return False

def format(s, l=None, nocolor=False):
    if l:
        s = s[:int(l)]
    if nocolor:
        return s
    return highlight(s, JsonLexer(), Terminal256Formatter())

class EnvironmentList(object):
    @staticmethod
    def print_list():
        path = "%s/.tumbo" % os.path.expanduser("~")
        table = []
        if not os.path.exists(path):
            os.mkdir(path) 
        for file in os.listdir(path):
            if ".json" in file:
                envId = file.replace(".json", "")
                env = Env.load(envId)
                table.append([envId, env.config_data['url'], env.active_str, env.config_data['username']])
        print tabulate(table, headers=['ID', 'URL', 'active', 'User'])

    @staticmethod
    def get_active(env=None):
        if not env:
            try:
                active_envId = os.path.basename(os.readlink("%s/.tumbo/active_env" % os.path.expanduser("~")).replace(".json", ""))
            except OSError:
                return None
        else:
            active_envId = env
        return Env.load(active_envId)


class Env(object):
    def __init__(self, envId, url=None):
        self.url = url
        self.envId = envId

        try:
            if self.envId+".json" in os.readlink("%s/.tumbo/active_env" % os.path.expanduser("~")):
                self.active = True
                self.active_str = "*"
            else:
                self.active_str = ""
                self.active = False
        except OSError:
            self.active_str = ""
            self.active = False

    def _call_api(self, url, method="GET", params=None, json=None):
        try:
            r = requests.request(method, self.config_data['url']+url,
                                 #allow_redirects=False,
                                 headers={
                                    'Authorization': "Token %s" % self.config_data['token']
                                 },
                                 params=params,
                                 json=json
                                 )
            response = r.json() if 'Content-Type' in r.headers and "json" in r.headers['Content-Type'] else r.text
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print "Error (%s)" % e.message
            print response
            sys.exit(1)
        except requests.exceptions.ConnectionError:
            print "Could not connect to %s" % self.config_data['url']
            sys.exit(1)
        return r.status_code, response

    def _gettoken(self):
        url = self.url + "/core/api/api-token-auth/"
        r = requests.post(url, data={'username': self.user, 'password': self.password})

        if r.status_code != 200:
            print "Wrong username/password for '%s'" % self.url
            sys.exit(1)
        else:
            token = r.json()['token']
        return token

    def _getcredentials(self):
        self.user = getpass.getpass(prompt="Username: ")
        self.password = getpass.getpass()

    @property
    def config_path(self):
        path = "%s/.tumbo" % os.path.expanduser("~")
        if not os.path.exists(path):
            os.mkdir(path)
        config_path = "%s/%s.json" % (path, self.envId)
        return config_path

    def login(self):

        self._getcredentials()

        with open(self.config_path, 'w+') as config_file:
            try:
                self.config_data = json.load(config_file)
            except ValueError:
                self.config_data = {}
            self.config_data['env'] = self.envId
            self.config_data['username'] = self.user
            self.config_data['token'] = self._gettoken()
            self.config_data['url'] = self.url

            config_file.write(json.dumps(self.config_data))
            config_file.close()
            if "lchmod" in os.__dict__:
                os.lchmod(self.config_path, 0600)
            else:
                os.chmod(self.config_path, 0600)
            print "Logged in to '%s' with '%s' successfully" % (self.envId, self.user)

    def logout(self):
        try:
            os.remove(self.config_path)
            print "Logged out"
        except OSError:
            print "Not logged in"

    def switch(self):
        pass

    @staticmethod
    def load(envId):
        path = "%s/.tumbo" % os.path.expanduser("~")
        if not os.path.exists(path):
            os.mkdir(path)
        config_path = "%s/%s.json" % (path, envId)
        with open(config_path, 'r') as config_file:
            try:
                config_data = json.load(config_file)
            except ValueError:
                pass

            id = Env(envId)
            id.config_data = config_data
            return id

    def __str__(self):
        self.envId = "* "+self.envId if self.active else self.envId
        return "%-20s   %-30s" % (self.envId, self.config_data['url'])

    def set_active(self):
        link = "%s/.tumbo/active_env" % os.path.expanduser("~")
        if os.path.exists(link):
            os.remove(link)
        os.symlink(self.config_path, link)

    def open_browser(self, base=None):
        import webbrowser
        if not base:
            url = "%s/core" % self.config_data['url']
        else:
            url = "%s/core/base/%s/index" % (self.config_data['url'], base)
        webbrowser.open(url+"/")

    def projects_list(self):
        status_code, projects = self._call_api("/core/api/base/")
        table = []
        for project in projects:
            state = "Running" if project['state'] else "Stopped"
            if len(project['executors']) > 0:
                state = state + " (%s) " % str(project['executors'][0]['pid'])
            table.append([project['name'], state])
        print tabulate(table, headers=["Projectname", "State"])

    def project_create(self, name):
        status_code, response = self._call_api("/core/api/base/", method="POST", json={"name": name})
        if status_code == 201:
            print "Project %s created" % (name)
        else:
            print status_code

    def project_stop(self, name):
        status_code, projects = self._call_api("/core/api/base/%s/stop/" % name, method="POST")
        if status_code == 200:
            print "Project %s stopped" % name

    def project_start(self, name):
        status_code, projects = self._call_api("/core/api/base/%s/start/" % name, method="POST")

    def project_destroy(self, name):
        status_code, projects = self._call_api("/core/api/base/%s/destroy/" % name, method="POST")
        if status_code == 200:
            print "Project executor destroyed"

    def project_delete(self, name):
        status_code, projects = self._call_api("/core/api/base/%s/delete/" % name, method="POST")
        if status_code == 200:
            print "Project %s deleted" % name
        else:
            print "Error: Could not delete Project %s" % name

    def project_show(self, name):
        status_code, project = self._call_api("/core/api/base/%s/" % name)
        print "\nStatus\n******"
        state = "Running" if project['state'] else "Stopped"
        print state

        print "\nExecutors\n*******"
        table = []
        for executor in project['executors']:
            table.append([
                executor['port'],
                executor['ip'] + " / " + executor['plugins'].get('dnsnameplugin', {}).get('SERVICE_DNS_V4', ""),
                str(executor['ip6']) + " / " + executor['plugins'].get('dnsnameplugin', {}).get('SERVICE_DNS_V6', ""),
            ])

        print tabulate(table, headers=["Port", "IPv4", "IPv6"])

        status_code, functions = self._call_api("/core/api/base/%s/apy/" % name)
        if status_code == 404:
            print "Project does not exist"
            return

        status_code, settings = self._call_api("/core/api/base/%s/setting/" % name)
        print "\nSettings\n********"
        table = []
        for setting in settings:
            public = "Yes" if setting['public'] else "No"
            table.append([setting['key'], public, setting['value']])
        print tabulate(table, headers=["Key", "Public", "Value"])

        print "\nFunctions\n*********"
        table = []
        for function in functions:
            schedule = function['schedule'] if function['schedule'] else ""
            executed = function['counter']['executed'] if function.get("counter") else 0
            failed = function['counter']['failed'] if function.get("counter") else 0
            public = "Yes" if function['public'] else "No"
            table.append([
                function['name'],
                public,
                schedule,
                executed,
                failed
            ])
        print tabulate(table, headers=["Name", "Public", "Schedule", "Counter success", "Counter failed"])

    def project_transactions(self, name, tid=None):
        data = {}
        if tid:
            data['rid'] = tid
        status_code, transactions = self._call_api("/core/api/base/%s/transactions/" % name, method="GET", params=data)

        logs_only = arguments.get('--logs', False)
        cut = arguments.get('--cut', None)
        nocolor = arguments.get('--nocolor', False)

        for transaction in transactions:
            rid = transaction['rid']
            table = []
            if not logs_only:
                tin = pprint.pformat(transaction['tin'], indent=8)
                tin = format(tin, cut, nocolor)
                tout = pprint.pformat(transaction['tout'], indent=8)
                tout = format(tout, cut, nocolor)
                table.append([
                    "In", transaction['created'], tin[:5000]
                ])
            for log in transaction['logs']:
                created = tolocaltime(log['created'])
                level = int(log['level'])
                if level == logging.DEBUG:
                            level_s = "DEBUG"
                elif level == logging.INFO:
                            level_s = "INFO"
                elif level == logging.WARNING:
                            level_s = "WARNING"
                elif level == logging.ERROR:
                            level_s = "ERROR"
                elif level == logging.CRITICAL:
                            level_s = "CRITICAL"
                else:
                            level_s = "UNKNOWN"
                table.append([
                    "Log (%s)" % level_s, created, format(log['msg'], cut, nocolor)
                ])
            if not logs_only:
                table.append([
                    "Out", tolocaltime(transaction['modified']), format(tout, cut, nocolor)
                ])
            print tabulate(table, headers=[rid, "Date", "Type"], tablefmt="simple")

    def create_function(self, project_name, function_name):
        status_code, response = self._call_api("/core/api/base/%s/apy/" % (project_name), method="POST", json={"name": function_name})
        if status_code == 201:
            print "Function %s/%s created" % (project_name, function_name)

    def edit_function(self, project_name, function_name):
        status_code, response = self._call_api("/core/api/base/%s/apy/%s" % (project_name, function_name), method="GET")
        file, path = tempfile.mkstemp()
        f = open(path, "w")
        f.write(response['module'])
        f.close()
        from subprocess import call
        print path
        call(["/usr/bin/vim", path])

        if confirm():

            f = open(path, "r")
            status_code, response = self._call_api("/core/api/base/%s/apy/%s/" % (project_name, function_name), method="PATCH", json={'module': f.read()})
            if status_code == 200:
                print "Saved"
            #if status_code == 201:
            #    print "Function %s/%s created" % (project_name, function_name)
            #status_code, response = self._call_api("/core/api/base/%s/apy/" % (project_name), method="POST", json={"name": function_name})


    def execute(self, project_name, function_name, async=False):
        if not async:
            status_code, response = self._call_api("/core/api/base/%s/apy/%s/execute/?json" % (project_name, function_name))
        else:
            status_code, response = self._call_api("/core/api/base/%s/apy/%s/execute/?json=&async=" % (project_name, function_name))
            print "Started with id '%s'" % response['rid']
        state_url = response.get('url', None)
        if not state_url and response['status'] == "OK":
            pass
        else:
            while True:
                status_code, response = self._call_api(state_url)
                state = response['status']
                if state != "RUNNING":
                    break
                sys.stdout.write('.')
                sys.stdout.flush()
                time.sleep(2)

        response = response[:1000]+"... truncated ..." if len(response) > 999 else response
        print "HTTP Status Code: %s" % status_code
        sys.stdout.write("Response: ")
        nocolor = arguments.get('--nocolor', False)
        respone = pprint.pformat(response, indent=4)
        nocolor = arguments.get('--nocolor', False)
        if type(response) is dict:
            response = json.dumps(response)
        print format(response, nocolor=nocolor)


def do_ngrok():
    time.sleep(1)
    ngrok_hostname = arguments.get("--ngrok-hostname", None)
    ngrok_authtoken = arguments.get("--ngrok-authtoken", None)
    print "Starting ngrok for %s with %s" % (ngrok_hostname, ngrok_authtoken)
    if arguments['docker']:
        port = docker_compose("-p", "tumboserver", "-f", compose_file, "port", "app", "80").split(":")[1]
    else:
        port = 8000
    cmd = '-hostname=%s -authtoken=%s localhost:%s' % (ngrok_hostname, ngrok_authtoken, port)
    ngrok(cmd.split(), _out="/dev/null", _err="/dev/stderr", _bg=True)


def tolocaltime(dt):
    from datetime import datetime
    import pytz     # $ pip install pytz
    import tzlocal  # $ pip install tzlocal

    local_timezone = tzlocal.get_localzone() # get pytz tzinfo
    utc_time = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S.%fZ")
    local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(local_timezone)
    return local_time


if __name__ == '__main__':
    arguments = docopt(__doc__, version="0.4.3")
    if arguments['--ngrok-hostname'] and arguments['docker']:
        try:
            ngrok = sh.Command("ngrok")
        except sh.CommandNotFound:
            print "ngrok is not installed"
            ngrok = None

    time.sleep(0.5)
    if arguments['env']:
        if arguments['login']:
            env = Env(arguments['<env-id>'], arguments['<url>'])
            env.login()

        if arguments['logout']:
            env = Env(arguments['<env-id>'])
            env.logout()

        if arguments['list']:
            EnvironmentList.print_list()

        if arguments['active']:
            Env(arguments['<env-id>']).set_active()

        if arguments['open']:
            Env.load(arguments['<env-id>']).open_browser()

    if arguments['project']:
        envId = arguments.get('--env', None)
        env = EnvironmentList.get_active(env=envId)

        if arguments['list']:
            env.projects_list()
        if arguments['<base-name>']:

            if arguments['create'] and not arguments['function']:
                env.project_create(arguments['<base-name>'])

            if arguments['delete'] and not arguments['function']:
                env.project_delete(arguments['<base-name>'])

            if arguments['stop']:
                env.project_stop(arguments['<base-name>'])

            if arguments['restart']:
                env.project_stop(arguments['<base-name>'])
                time.sleep(2)
                env.project_start(arguments['<base-name>'])

            if arguments['destroy']:
                env.project_destroy(arguments['<base-name>'])

            if arguments['start']:
                env.project_start(arguments['<base-name>'])
                env.project_show(arguments['<base-name>'])

            if arguments['show'] and not arguments['function']:
                env.project_show(arguments['<base-name>'])

            if arguments['open']:
                env.open_browser(base=arguments['<base-name>'])

            if arguments['function']:

                if arguments['<function-name>']:
                    if arguments['execute']:
                        env.execute(arguments['<base-name>'], arguments['<function-name>'], async=arguments['--async'])

                    if arguments['create']:
                        env.create_function(arguments['<base-name>'], arguments['<function-name>'])

                    if arguments['edit']:
                        env.edit_function(arguments['<base-name>'], arguments['<function-name>'])

            if arguments['transactions']:
                tid = arguments.get('--tid', None)
                print env.project_transactions(arguments['<base-name>'], tid)

    if arguments['server']:
        if arguments['dev']:
            if arguments['run']:

                def stop_handler(signum, frame):
                    stop()

                def stop():
                    try:
                        os.killpg(app.pid, 2)
                        for pid in background_pids:
                            os.killpg(pid, signal.SIGTERM)
                        if arguments['--coverage']:
                            sh.coverage("combine")
                    except OSError:
                        pass
                    try:
                        for pid in sh.pgrep('-f', 'python.*worker.*').split():
                            os.killpg(int(pid), 9)

                        sh.pkill("ngrok")
                    except sh.ErrorReturnCode_1:
                        pass

                    print "Stopped"
                signal.signal(signal.SIGTERM, stop_handler)

                if arguments['--autostart']:
                    print "Starting postgresql"
                    cmd_args = '-u postgres /usr/bin/postgres -D /var/lib/pgsql/data'
                    sudo = sh.Command("sudo")
                    cmd = sudo(cmd_args.split(), _out="/dev/stdout", _err="/dev/stderr", _bg=True)

                    print "Starting redis"
                    cmd_args = "-u redis /usr/bin/redis-server /etc/redis.conf"
                    sudo(cmd_args.split(), _out="/dev/stdout", _err="/dev/stderr", _bg=True)

                    print "Starting rabbitmq"
                    cmd_args = "-u rabbitmq /usr/sbin/rabbitmq-server"
                    sudo(cmd_args.split(), _out="/dev/stdout", _err="/dev/stderr", _bg=True)

                print "Starting development server"
                env = {}
                env.update(os.environ)
                env.update({'PYTHONPATH': "fastapp", 'CACHE_ENV_REDIS_PASS': "asdf123asdf123567sdf1238908898989",
                                   'DROPBOX_CONSUMER_KEY': os.environ['DROPBOX_CONSUMER_KEY'],
                                   'DROPBOX_CONSUMER_SECRET': os.environ['DROPBOX_CONSUMER_SECRET'],
                                   'DROPBOX_REDIRECT_URL': os.environ['DROPBOX_REDIRECT_URL'],
                           })
                PROPAGATE_VARIABLES = os.environ.get("PROPAGATE_VARIABLES", None)
                if PROPAGATE_VARIABLES:
                    env['PROPAGATE_VARIABLES'] = PROPAGATE_VARIABLES

                cmd = "%s syncdb --noinput --settings=tumbo.dev" % manage_py
                syncdb = python(cmd.split(), _env=env, _out="/dev/stdout", _err="/dev/stderr", _bg=True)
                syncdb.wait()

                cmd = "%s makemigrations core --settings=tumbo.dev" % manage_py
                if arguments['--coverage']:
                    cmd = coverage_cmd + cmd
                migrate = python(cmd.split(), _env=env, _out="/dev/stdout", _err="/dev/stderr", _bg=True)
                migrate.wait()

                cmd = "%s migrate --settings=tumbo.dev" % manage_py
                if arguments['--coverage']:
                    cmd = coverage_cmd + cmd
                migrate = python(cmd.split(), _env=env, _out="/dev/stdout", _err="/dev/stderr", _bg=True)
                migrate.wait()

                cmd = "%s  migrate aaa --settings=tumbo.dev" % manage_py
                if arguments['--coverage']:
                    cmd = coverage_cmd + cmd
                migrate = python(cmd.split(), _env=env, _out="/dev/stdout", _err="/dev/stderr", _bg=True)
                migrate.wait()

                try:
                    cmd = "%s create_admin --username=admin --password=adminpw --email=info@localhost --settings=tumbo.dev" % manage_py
                    adminuser = python(cmd.split(), _env=env, _out="/dev/stdout", _err="/dev/null", _bg=True)
                    adminuser.wait()
                except Exception, e:
                    print e
                    print "adminuser already exists?"

                cmd = "%s import_base --username=admin --file %s/examples/generics.zip  --name=generics --settings=tumbo.dev" % (manage_py, tumbo_path)
                if arguments['--coverage']:
                    cmd = coverage_cmd + cmd
                generics_import = python(cmd.split(), _env=env, _out="/dev/stdout", _err="/dev/stderr", _bg=True)

                background_pids = []

                for mode in ["cleanup", "heartbeat", "async", "log", "scheduler"]:
                    cmd = "%s heartbeat --mode=%s --settings=tumbo.dev" % (manage_py, mode)
                    if arguments['--coverage']:
                        cmd = coverage_cmd + cmd
                    background = python(cmd.split(), _env=env, _out="/dev/stdout", _err="/dev/stderr", _bg=True)
                    background_pids.append(background.pid)

                cmd = "%s runserver 0.0.0.0:8000 --settings=tumbo.dev" % manage_py
                if arguments['--coverage']:
                    cmd = coverage_cmd + cmd

                app = python(cmd.split(), _env=env, _out="/dev/stdout", _err="/dev/stderr", _tty_in=True, _in=sys.stdin, _bg=True, _cwd="/home/philipsahli/workspace/tumbo-server")

                if arguments['--ngrok-hostname'] and arguments['docker']:
                    if not ngrok:
                        print "Install ngrok first"
                        sys.exit(1)
                    do_ngrok()

                try:
                    app.wait()
                except (KeyboardInterrupt, sh.ErrorReturnCode_1, Exception), e:
                    stop()

            if 'test' in arguments:
                print "Testing example on Docker"

                r = requests.post("http://localhost:8000/core/api/api-token-auth/", data={'username': "admin", 'password': "admin"})
                token = r.json()['token']
                print token
                r = requests.post("http://localhost:8000/core/api/base/87/start/", headers={
                    'Authorization': "Token " + token
                })
                print r.text
                print r.status_code
                time.sleep(5)
                r = requests.get("http://localhost:8000/core/base/example/exec/foo/?json", headers={
                    'Authorization': "Token " + token
                })
                print r.text
                print r.json()

        if arguments['docker']:
            if arguments['pull']:
                print "Docker images pull ..."
                cmd = "-p tumboserver -f %s pull" % compose_file_base
                docker_compose(cmd.split(), _out="/dev/stdout", _err="/dev/stderr")
                print "Docker images pull done."

            if arguments['build']:
                print "Build docker images"

                cmd = "bin/create_package.sh"
                create_package = bash(cmd.split(), _out="/dev/stdout", _err="/dev/stderr")
                create_package.wait()

                cmd = "-p tumboserver -f %s build --pull" % compose_file
                build = docker_compose(cmd.split(), _out="/dev/stdout", _err="/dev/stderr")
                build.wait()

            if arguments['stop']:
                print "Stop docker containers"

                cmd = "-p tumboserver -f %s stop" % compose_file
                build = docker_compose(cmd.split(), _out="/dev/stdout", _err="/dev/stderr")
                build.wait()

                cmd = "-p tumboserver -f %s stop" % compose_file_base
                build = docker_compose(cmd.split(), _out="/dev/stdout", _err="/dev/stderr")
                build.wait()

            if arguments['logs']:
                print "Follow logs of docker containers"

                cmd = "-p tumboserver -f %s logs -f" % compose_file
                build = docker_compose(cmd.split(), _out="/dev/stdout", _err="/dev/stderr")
                build.wait()

            if arguments['run']:
                print "Starting Tumbo on Docker"
                if arguments['--stop-after']:
                    print "Will stop after %s seconds" % arguments['--stop-after']

                try:
                    cmd = "-p tumboserver -f %s up -d --no-recreate" % compose_file_base
                    base = docker_compose(cmd.split(), _out="/dev/stdout", _err="/dev/stderr")
                    time.sleep(40)

                    cmd = "-p tumboserver -f %s up" % compose_file
                    app = docker_compose(cmd.split(), _out="/dev/stdout", _err="/dev/stderr", _bg=True, _env=os.environ)

                    if arguments['--ngrok-hostname']:
                        time.sleep(10)
                        ngrok()

                    if arguments['--stop-after']:
                        print "Sleeping for %s seconds" % arguments['--stop-after']
                        time.sleep(int(arguments['--stop-after']))
                        raise Exception("Stopping after %s" % arguments['--stop-after'])
                    else:
                        app.wait()

                except (KeyboardInterrupt, sh.ErrorReturnCode_1, Exception), e:
                    print e
                    # stop workers
                    cmd = "-p tumboserver -f %s kill" % compose_file
                    app = docker_compose(cmd.split(), _out="/dev/stdout", _err="/dev/stderr")

                    cmd = "-p tumboserver -f %s rm -f" % compose_file
                    app = docker_compose(cmd.split(), _out="/dev/stdout", _err="/dev/stderr")

                    cmd = "-p tumboserver -f %s kill" % compose_file
                    base = docker_compose(cmd.split(), _out="/dev/stdout", _err="/dev/stderr")

                    try:
                        sh.pkill("ngrok")
                        for line in sh.grep(sh.docker("ps", "-a"), "worker"):
                            sh.docker("kill", line.split()[0])
                            sh.docker("rm", line.split()[0])
                    except sh.ErrorReturnCode_1:
                        pass

    if arguments['docker'] and arguments['url']:
        port = docker_compose("-p", "tumboserver", "-f", compose_file, "port", "app", "80").split(":")[1]
        print("http://%s:%s" % ("localhost", port))
