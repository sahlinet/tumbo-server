#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Tumbo

Usage:
  tumbo.py server dev run [--ngrok-hostname=host] [--ngrok-authtoken=token] [--autostart]
  tumbo.py server dev test
  tumbo.py server docker build
  tumbo.py server docker run [--stop-after=<seconds>][--worker=worker] [--ngrok-hostname=host] [--ngrok-authtoken=token]
  tumbo.py server docker stop
  tumbo.py server docker test
  tumbo.py server docker pull
  tumbo.py server docker url
  tumbo.py server docker logs
  tumbo.py server tutum run [--worker=worker] [--ngrok-hostname=host] [--ngrok-authtoken=token]
  tumbo.py env list
  tumbo.py env <env-id> login <url>
  tumbo.py env <env-id> logout
  tumbo.py env <env-id> active
  tumbo.py env <env-id> open
  tumbo.py project list
  tumbo.py project <base-name> show
  tumbo.py project <base-name> open
  tumbo.py project <base-name> start
  tumbo.py project <base-name> stop
  tumbo.py project <base-name> restart
  tumbo.py project <base-name> destroy
  tumbo.py project <base-name> delete
  tumbo.py project <base-name> create
  tumbo.py project <base-name> transport <env>
  tumbo.py project <base-name> function <function-name> execute [--async] [--public]
  tumbo.py project <base-name> function <function-name> show
  tumbo.py project <base-name> transactions [--tid=<tid>]  [--logs]
  tumbo.py project <base-name> export [filename]
  tumbo.py project <base-name> import <zipfile>
  # tumbo.py project <name> settings edit
  # tumbo.py project <name> datastore <show>
  # tumbo.py --version

Options:
  -h --help         Show this screen.
  --version         Show version.
  --worker=worker   How to start the worker, can be 'spawn', 'docker' or 'rancher'.

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
import thread
import logging

from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import Terminal256Formatter


from docopt import docopt
from os.path import expanduser
from tabulate import tabulate

docker_compose = sh.Command("docker-compose")
python = sh.Command(sys.executable)

def format(s):
	return highlight(s, JsonLexer(), Terminal256Formatter())

class EnvironmentList(object):
    @staticmethod
    def print_list():
        path = "%s/.tumbo" % expanduser("~")
        table = []
        if not os.path.exists(path):
            os.mkdir(path) 
        for file in os.listdir(path):
            if ".json" in file:
                envId = file.replace(".json", "")
                env = Env.load(envId)
                table.append([envId, env.config_data['url'], env.active_str])
        print tabulate(table, headers=['ID', 'URL', 'active'])

    @staticmethod
    def get_active():
        try:
            active_envId = os.path.basename(os.readlink("%s/.tumbo/active_env" % expanduser("~")).replace(".json", ""))
        except OSError:
            return None
        return Env.load(active_envId)


class Env(object):
    def __init__(self, envId, url=None):
        self.url = url
        self.envId = envId

        try:
            if self.envId+".json" in os.readlink("%s/.tumbo/active_env" % expanduser("~")):
                self.active = True
                self.active_str = "*"
            else:
                self.active_str = ""
                self.active = False
        except OSError:
            self.active_str = ""
            self.active = False

    def _call_api(self, url, method="GET", data=None):
        try:
            r = requests.request(method, self.config_data['url']+url,
                                 #allow_redirects=False,
                                 headers={
                                 'Authorization':
                                 "Token %s" % self.config_data['token']
                                 },
				 params=data
                                 )
            response = r.json() if 'Content-Type' in r.headers and "json" in r.headers['Content-Type'] else r.text
	    r.raise_for_status()
	except requests.exceptions.HTTPError as e:
            print "Error (%s)" % e.message
            sys.exit(1)
        except requests.exceptions.ConnectionError:
            print "Could not connect to %s" % self.config_data['url']
            sys.exit(1)
        return r.status_code, response

    def _gettoken(self):
        url = self.url + "/core/api-token-auth/"
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
        path = "%s/.tumbo" % expanduser("~")
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
                pass
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
        path = "%s/.tumbo" % expanduser("~")
        if not os.path.exists(path):
            os.mkdir(path)
        config_path = "%s/%s.json" % (path, envId)
        #print config_path
        with open(config_path, 'r') as config_file:
            try:
                config_data = json.load(config_file)
            except ValueError:
                pass
                config_data = {}

            #print "return Env(envId)"
            #print config_data
            id = Env(envId)
            id.config_data = config_data
            return id

    def __str__(self):
        self.envId = "* "+self.envId if self.active else self.envId
        return "%-20s   %-30s" % (self.envId, self.config_data['url'])

    def set_active(self):
        link = "%s/.tumbo/active_env" % expanduser("~")
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
            table.append([project['name'], state])
        print tabulate(table, headers=["Projectname", "State"])

    def project_stop(self, name):
        status_code, projects = self._call_api("/core/api/base/%s/stop/" % name, method="POST")

    def project_start(self, name):
        status_code, projects = self._call_api("/core/api/base/%s/start/" % name, method="POST")

    def project_destroy(self, name):
        status_code, projects = self._call_api("/core/api/base/%s/destroy/" % name, method="POST")

    def project_delete(self, name):
        status_code, projects = self._call_api("/core/base/%s/delete/" % name, method="POST")

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
	data={}
	if tid:
		data['rid'] = tid
        status_code, transactions = self._call_api("/core/api/base/%s/transactions/" % name, method="GET", data=data)
	import pprint
	logs_only = arguments.get('--logs', False)
	for transaction in transactions:
		rid=transaction['rid']
        	table = []
		if not logs_only:
			tin=pprint.pformat(transaction['tin'], indent=8)
			tin=format(tin)
			tout=pprint.pformat(transaction['tout'], indent=8)
			tout=format(tout)
			table.append([
				"In", transaction['created'], tin[:5000]
			])
		for log in transaction['logs']:
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

				"Log (%s)" % level_s, log['created'], log['msg']
			])
		if not logs_only:
			table.append([
				"Out", transaction['modified'], tout[:5000]
			])
        	print tabulate(table, headers=[rid, "Date", "Type"], tablefmt="simple")

    def execute(self, project_name, function_name, async=False):
        if not async:
            status_code, response = self._call_api("/core/api/base/%s/apy/%s/execute/?json" % (project_name, function_name))
        else:
            status_code, response = self._call_api("/core/api/base/%s/apy/%s/execute/?json=&async=" % (project_name, function_name))
        state_url = response.get('url', None)
        print "Started with id '%s'" % response['rid']
        if not state_url and response['status'] == "OK":
            pass
        else:
            while True:
                status_code, response = self._call_api(state_url)
                state = response['status']
		if state != "RUNNING":
			break
		#print "Still running..."
		sys.stdout.write('.')
		sys.stdout.flush()
		time.sleep(2)

        response = response[:1000]+"... truncated ..." if len(response) > 999 else response
        print "HTTP Status Code: %s" % status_code
        sys.stdout.write("Response: ")
	#print response
	response=pprint.pformat(response, indent=4)
	#print response
        print format(response)

def do_ngrok():
    time.sleep(1)
    ngrok_hostname = arguments.get("--ngrok-hostname", None)
    ngrok_authtoken = arguments.get("--ngrok-authtoken", None)
    print "Starting ngrok for %s with %s" % (ngrok_hostname, ngrok_authtoken)
    if arguments['docker']:
        port = docker_compose("-f", "docker-compose-app-docker_socket_exec.yml", "port", "app", "80").split(":")[1]
    else:
        port = 8000
    cmd = '-hostname=%s -authtoken=%s localhost:%s' % (ngrok_hostname, ngrok_authtoken, port)
    ngrok(cmd.split(), _out="/dev/null", _err="/dev/stderr", _bg=True)


if __name__ == '__main__':
    # arguments = docopt(__doc__, version=version)
    arguments = docopt(__doc__, version="0.1.16")
    #import pprint; pprint.pprint(arguments)
    if arguments['--ngrok-hostname'] and arguments['docker']:
	    try:
		ngrok = sh.Command("ngrok")
	    except sh.CommandNotFound:
		print "ngrok is not installed"
		ngrok = None

    time.sleep(0.5)
    if arguments['env']:
        #import pprint; pprint.pprint(arguments)
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
        env = EnvironmentList.get_active()
        #print arguments
        if arguments['list']:
            env.projects_list()
        if arguments['<base-name>']:
            if arguments['stop']:
                env.project_stop(arguments['<base-name>'])
                env.project_show(arguments['<base-name>'])

            if arguments['restart']:
                env.project_stop(arguments['<base-name>'])
                time.sleep(2)
                env.project_start(arguments['<base-name>'])
                env.project_show(arguments['<base-name>'])

            if arguments['destroy']:
                env.project_destroy(arguments['<base-name>'])
                env.project_show(arguments['<base-name>'])

            if arguments['delete']:
                env.project_delete(arguments['<base-name>'])

            if arguments['start']:
                env.project_start(arguments['<base-name>'])
                env.project_show(arguments['<base-name>'])

            if arguments['show']:
                env.project_show(arguments['<base-name>'])

            if arguments['open']:
                env.open_browser(base=arguments['<base-name>'])

            if arguments['function']:

                if arguments['<function-name>']:
                    if arguments['execute']:
                        env.execute(arguments['<base-name>'], arguments['<function-name>'], async=arguments['--async'])

            if arguments['transactions']:
		tid = arguments.get('--tid', None)
		print env.project_transactions(arguments['<base-name>'], tid)

    if arguments['server']:
        #print arguments
        if arguments['dev']:
            if arguments['run']:

                def stop_handler(signum, frame):
                    stop()

                def stop():
                    try:
                        os.killpg(app.pid, 9)
                        os.killpg(background.pid, 9)
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
                    #cmd.wait()
                    
                    print "Starting redis"
                    cmd_args = "-u redis /usr/bin/redis-server /etc/redis.conf"
                    sudo(cmd_args.split(), _out="/dev/stdout", _err="/dev/stderr", _bg=True)

                    print "Starting rabbitmq"
                    cmd_args = "-u rabbitmq /usr/sbin/rabbitmq-server"
                    sudo(cmd_args.split(), _out="/dev/stdout", _err="/dev/stderr", _bg=True)
                    #sys.exit(0)
                print "Starting development server"
                env = {}
                env.update(os.environ)
                env.update({'PYTHONPATH': "fastapp", 'CACHE_ENV_REDIS_PASS': "asdf123asdf123567sdf1238908898989",
                                   'DROPBOX_CONSUMER_KEY': os.environ['DROPBOX_CONSUMER_KEY'],
                                   'DROPBOX_CONSUMER_SECRET': os.environ['DROPBOX_CONSUMER_SECRET'],
                                   'DROPBOX_REDIRECT_URL': os.environ['DROPBOX_REDIRECT_URL'],
                           })
                PROPAGATE_VARIABLES = os.environ.get("PROPAGATE_VARIABLES", None)
                print PROPAGATE_VARIABLES
                if PROPAGATE_VARIABLES:
                    env['PROPAGATE_VARIABLES'] = PROPAGATE_VARIABLES
                

                cmd = "tumbo/manage.py syncdb --noinput --settings=tumbo.dev"
                syncdb = python(cmd.split(), _env=env, _out="/dev/stdout", _err="/dev/stderr", _bg=True)
                syncdb.wait()
              
                cmd = "tumbo/manage.py makemigrations core --settings=tumbo.dev"
                migrate = python(cmd.split(), _env=env, _out="/dev/stdout", _err="/dev/stderr", _bg=True)
                migrate.wait()

                cmd = "tumbo/manage.py migrate --settings=tumbo.dev"
                migrate = python(cmd.split(), _env=env, _out="/dev/stdout", _err="/dev/stderr", _bg=True)
                migrate.wait()

                #cmd = "tumbo/manage.py migrate aaa --settings=tumbo.dev"
                #migrate = python(cmd.split(), _env=env, _out="/dev/stdout", _err="/dev/stderr", _bg=True)
                #migrate.wait()


                try:
                	cmd = "tumbo/manage.py create_admin --username=admin --password=adminpw --email=info@localhost --settings=tumbo.dev"
                	adminuser = python(cmd.split(), _env=env, _out="/dev/stdout", _err="/dev/null", _bg=True)
                	adminuser.wait()
                except:
                	print "adminuser already exists?"

                cmd = "tumbo/manage.py import_base --username=admin --file example_bases/generics.zip  --name=generics --settings=tumbo.dev"
                generics_import = python(cmd.split(), _env=env, _out="/dev/stdout", _err="/dev/stderr", _bg=True)

                cmd = "tumbo/manage.py heartbeat --settings=tumbo.dev"
                background = python(cmd.split(), _env=env, _out="/dev/stdout", _err="/dev/stderr", _bg=True)

                cmd = "tumbo/manage.py runserver 0.0.0.0:8000 --settings=tumbo.dev"
                app = python(cmd.split(), _env=env, _out="/dev/stdout", _err="/dev/stderr", _tty_in=True, _in=sys.stdin, _bg=True)

                if arguments['--ngrok-hostname'] and arguments['docker']:
                    if not ngrok:
                        print "Install ngrok first"
                        sys.exit(1)
                    do_ngrok()

                try:
                    app.wait()
                except (KeyboardInterrupt, sh.ErrorReturnCode_1, Exception), e:
                    stop()

            if arguments['test']:
                print "Testing example on docker"

                r = requests.post("http://localhost:8000/core/api-token-auth/", data={'username': "admin", 'password': "admin"})
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
                cmd = "-f docker-compose-base.yml pull"
                docker_compose(cmd.split(), _out="/dev/stdout", _err="/dev/stderr")
                print "Docker images pull done."

            if arguments['build']:
                print "Build docker images"

                cmd = "-f docker-compose-app-docker_socket_exec.yml build --pull --no-cache"
                build = docker_compose(cmd.split(), _out="/dev/stdout", _err="/dev/stderr")

                build.wait()
            if arguments['stop']:
                print "Stop docker containers"

                cmd = "-f docker-compose-app-docker_socket_exec.yml stop"
                build = docker_compose(cmd.split(), _out="/dev/stdout", _err="/dev/stderr")
                build.wait()

                cmd = "-f docker-compose-base.yml stop"
                build = docker_compose(cmd.split(), _out="/dev/stdout", _err="/dev/stderr")
                build.wait()

            if arguments['logs']:
                print "Follow logs of docker containers"

                cmd = "-f docker-compose-app-docker_socket_exec.yml logs -f"
                build = docker_compose(cmd.split(), _out="/dev/stdout", _err="/dev/stderr")
                build.wait()

            if arguments['run']:
                print "Starting Tumbo on docker"
                if arguments['--stop-after']:
                    print "Will stop after %s seconds" % arguments['--stop-after']

                try:
                    cmd = "-f docker-compose-base.yml up -d --no-recreate"
                    base = docker_compose(cmd.split(), _out="/dev/stdout", _err="/dev/stderr")
                    time.sleep(40)

                    cmd = "-f docker-compose-app-docker_socket_exec.yml up"
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
                    cmd = "-f docker-compose-app-docker_socket_exec.yml kill"
                    app = docker_compose(cmd.split(), _out="/dev/stdout", _err="/dev/stderr")

                    cmd = "-f docker-compose-app-docker_socket_exec.yml rm -f"
                    app = docker_compose(cmd.split(), _out="/dev/stdout", _err="/dev/stderr")

                    cmd = "-f docker-compose-base.yml kill"
                    base = docker_compose(cmd.split(), _out="/dev/stdout", _err="/dev/stderr")

                    try:
                        sh.pkill("ngrok")
                        for line in sh.grep(sh.docker("ps", "-a"), "worker"):
                            sh.docker("kill", line.split()[0])
                            sh.docker("rm", line.split()[0])
                    except sh.ErrorReturnCode_1:
                        pass



    if arguments['docker'] and arguments['url']:
        port = docker_compose("-f", "docker-compose-app-docker_socket_exec.yml", "port", "app", "80").split(":")[1]
        print("http://%s:%s" % ("localhost", port))
