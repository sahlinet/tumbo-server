# User Guide

* * *

## Base

A Base is a runtime unit and is running in an isolated environment. It can have many Execs.

### Start and Stop

The Base needs to run to execute Execs and to deliver static files to the client.

### Export and Import

On the Base page you can export the configuration into a zip file. Later you
can create or update the base on the same or on other platform.

> If a Base contains a lot of static files, export and import might fail because of timeouts!

* * *

## Static Files

Place static files in a folder `static` on the Dropbox base directory. When a static file is
accessed, the file is read from your Dropbox and then cached on Tumbo for {{ TUMBO_STATIC_CACHE_SECONDS }} seconds.

{% verbatim %}
Static files can be accessed over `https://HOST/userland/USERNAME/PROJECT_NAME/static/FILE`.
The URL until the word *static* is available as variable in HTML files as {{ TUMBO_STATIC_URL }}.
{% endverbatim %}

Files are loaded from following locations (first match is served):


### Dropbox App Directory

{% verbatim %}
After connecting your Dropbox Account with Tumbo you find a directory {{ TUMBO_DROPBOX_APP_NAME }}. When creating a project a directory is created. Place in it a directory static with files.
{% endverbatim %}

### Python Module installed in Worker

Create a Python Module with a directory static in it and install the module in your worker:


    def func(self, r=""):
        import os, sys
        module = "-e " + self.settings.GIT_URL
        pip = os.path.join(os.path.dirname(sys.executable), "pip")
            r=os.popen("%s install --upgrade %s" % (pip, module)).read()
        return r


###

* * *

## Exec

An Exec is function, which can be called by an HTTP Request to `https://HOST/userland/USERNAME/johndoe/helloworld/api/apy/greet`.

### Editing

You can edit the Execs in the browser editor or in the Dropbox base folder.

An Exec is always a function named `func` with an argument:

    def func(self):
        return True

The single argument, here called self, contains data about the request and has functions attached:

If the Exec has changed on Dropbox, it will be refreshed on *Tumbo* automatically. This can take up to 30 seconds.

### Initialize

If you need to install i.e. Python modules or do any specific work in a base after startup, you can use this feature. On startup of a base the exec with the name `init` is called with a HTTP GET Request.


### Logging

From within python code write log messages with following line:

`self.error(self.rid, "error")`

`self.warn(self.rid, "warn")`

`self.info(self.rid, "info")`

`self.debug(self.rid, "debug")`

The log messages are attached to the transaction and Tumbo's *CLi* displays the log:

    tumbo-cli.py project helloworld transactions


### Siblings

Siblings are Exec's in the same base and are available for execution on `self.siblings.NAME`.

    def func(self):
        return self.siblings.another_exec(self)

### Request Arguments

In the Exec following request data is available:

* HTTP Request Method `self.method`

* HTTP Header Content-Type `self.content_type`

* GET parameters `self.GET`

* POST parameters `self.POST`

* Clients IP Address `self.REMOTE_ADDR`

* Users identity

The users identity call is available on `self.identiy` as dictionary:

    {
        "username": "user1",
        "type": "AuthenticatedUser",
        "email": "user1@example.com",
        "internalid": "177899378"
    }

Type can be AuthenticatedUser or AnonymousUser.


### Responses

#### HTML (text/html)

    def func(self):
        return self.responses.HTMLResponse("<html><body>Hello World</body></html>")

#### JSON (application/json)

    def func(self):
        return self.responses.JSONResponse("{'a': 'b'}")

#### XML (application/xml)

    def func(self):
        return self.responses.XMLResponse("<note><text>hello</text></note>")

#### HTTP Redirect

    def func(self):
        return self.responses.RedirectResponse("http://another-url")

### Actions

On a response an action with the string "RESTART" can be added to restart the Base.

    def func(self):
        return self.responses.JSONResponse({'status': "installed"}, action="RESTART")

### Sharing

#### Shared Exec's

You can make an Exec public. Public Exec's can be related to a Base.

Related Exec's are available at `self.foreigns` as attribute.

    def func(self):
        return self.foreigns.yum_install(self)

### With Shared Key

Every base has a Shared-Key. Non-public bases can be used for anonymous users with providing a Querystring `shared_key`.

### Public

A public base can be accessed and used by anonymous users.
This configuration setting is for security reasons not exported. A base must be made public explicit.

### Execution

#### Curl

     curl -L -v "https://tumbo.example.com/userland/admin/base/hello-world/exec/echo/?json=&shared_key=f241fcab-0323-42b5-ac17-94bfefd5df72"
     {
	   "status": "OK",
	   "exception": null,
	   "returned": null,
	   "response_class": null,
	   "time_ms": "98",
	   "exception_message": null,
	   "rid": 17941542,
	   "id": "echo"
	 }

If the Exec raises an Exception the response status is `NOK`.

     curl -L -v "https://tumbo.example.com/userland/base/hello-world/exec/echo/?json=&shared_key=f241fcab-0323-42b5-ac17-94bfefd5df72"
	 {
       "status": "NOK",
       "exception": "Exception",
       "returned": null,
       "response_class": null,
       "time_ms": "344",
       "exception_message": "this text is raised",
       "rid": 41447693,
       "id": "echo"
     }

#### Browser

With the button *execute* the exec is always executed with a HTTP GET request. The response is visible in the log window.

#### Asynchronous

`&async`

When the key *async* is specified as query string, the client receives immediately a  'HTTP response status code 301 Moved Permanently' response.
The response refers to a location which is enriched with a query string `rid` (request id). With this URL the client can poll and
wait until the `status` is `FINISHED`.

### Schedules

Add in the UI a configuration for a scheduled execution of a function. For example `*/30 * * *` (`second minute our day_of_week`).


* * *

## Settings

{% verbatim %}
The settings you configured in a Base are rendered in static files ending with `.html` when used as `{{ SETTING_KEY }}` or
in python code in a exec as `self.settings.SETTING_KEY`.
{% endverbatim %}

* * *

## Access Control

*TODO*

### Core

### Userland

### Static

### Apy's

## Service Port

For every worker a service port is reserved. This let's you for example to run a webserver or any other daemon.

### Port

    print os.environ['SERVICE_PORT']

### IP

To know on which IP address the service is reachable, get the following variable:

    print os.environ['SERVICE_IP']

Use `SERVICE_IP6` for the IPv6 address.

### DNS

A host record is registered in a DNS zone in the form:

    USERNAME-BASENAME-INSTANCE_NUM[-V4,-V6].ZONE

Examples:

IPv4 (A) and IPv6 (AAAA) record:

    print os.environ['SERVICE_DNS']
    johndoe-helloworld-0.ZONE

IPv4 only:

    print os.environ['SERVICE_DNS_V4']
    johndoe-helloworld-0-v4.ZONE

IPv6 only:

    print os.environ['SERVICE_DNS_V6']
    johndoe-helloworld-0-v6.ZONE

* * *

## Datastore

The datastore lets you store and access data per base. The data get retained over base lifecycle.
On `init` the datastore is not yet available.

### API

#### Store JSON data

    data = {"name": "Rolf"}
    self.datastore.write_dict(data)


#### Get all stored data

    results = self.datastore.all()
    for row in results:
         print row


#### Filter data

Per value in key

    self.datastore.filter("name", "Rolf")


##### Get one row

    self.datastore.get("name", "Rolf")


#### Update one row

    result_obj = self.datastore.get("function", "setUp")
    result_obj.data['function'] = "tearDown"
    self.datastore.save(result_obj)


#### Delete one row

    row = self.datastore.get("name", "Rolf")
    self.datastore.delete(row)


### Static Files

You can access the data in the static files. The data is rendered on server-side.

{% verbatim %}

    <!DOCTYPE html>
    <html>
    <body>
        <h1>Hello World</h1>
        <ul>
        {% for obj in datastore.all %}
            <li>
            Obj: {{ obj.data.name }} ({{ obj.created_on }})
            </li>
        {% endfor %}
        </ul>
    </body>
    </html>

{% endverbatim %}

For querying only data for a logged in user, use the templatetag ˋdata_for_userˋ:

{% verbatim %}
    {% load datastore %}
    {% data_for_user as data %}
{% endverbatim %}
* * *

## Transport

Transporting from one *Tumbo* platform to another uses internally the export and import feature.
On the source platform you have to configure the transport endpoint, the token and how to handle settings.

Then you can transport a Base to the target platform from the base page.

    https://HOST/fastapp/api/base/import/

* * *

## Development

How you can run *Tumbo* as lite-version on your machine is documented on [github.com/sahlinet/tumbo-server](https://github.com/sahlinet/tumbo-server)

## HTTP API

### Authorization

The API uses an authentication mechanism with a per user token. HTTP-Requests to the API must include a header like:

    Authorization: Token YOUR-TOKEN

The token can be grabbed from your profile page.

### API Docs

<a target="_blank" href="{% url 'api-docs' %}#!/api">API Documentation</a>
