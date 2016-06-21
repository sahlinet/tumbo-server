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
accessed by a client, the file is read from your Dropbox and then cached on Tumbo for {{ FASTAPP_STATIC_CACHE_SECONDS }} seconds.

{% verbatim %}
Static files can be accessed over `https://tumbo.example.com/fastapp/EXAMPLE_BASE/static/FILE`. The
URL until the word *static* is available as variable in HTML files as {{ FASTAPP_STATIC_URL }}.
{% endverbatim %}

* * *

## Exec

An Exec is function, which can be called by an HTTP Request.

### Editing

You can edit the Execs in the browser editor or in the Dropbox base folder.

An Exec is always a function named `func`:

    def func(self):
        return True

If the Exec has changed on Dropbox, it will be refreshed on *Tumbo* automatically. This
can take up to 30 seconds.

### Initialize

If you need to install i.e. Python modules or do any specific work in a base after startup, you can use this feature. On startup of a base the exec with the name `init` is called with a HTTP GET Request.


### Logging

From within python code write log messages with following line:

`self.error(self.rid, "error")`

`self.warn(self.rid, "warn")`

`self.info(self.rid, "info")`

`self.debug(self.rid, "debug")`

### Siblings

Siblings are Exec's in the same base and are available for execution on `self.siblings.NAME`.

    def func(self):
        return self.siblings.another_exec(self)

### Request Arguments

In the Exec some basic data about the request is available:

* Username of authenticated user `self.user`

* HTTP Request Method `self.method`

* HTTP Header Content-Type `self.content_type`

* GET parameters `self.GET`

* POST parameters `self.POST`

* Clients IP Address `self.REMOTE_ADDR`

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

     curl -L -v "https://tumbo.example.com/fastapp/base/hello-world/exec/echo/?json=&shared_key=f241fcab-0323-42b5-ac17-94bfefd5df72"
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

     curl -L -v "https://tumbo.example.com/fastapp/base/hello-world/exec/echo/?json=&shared_key=f241fcab-0323-42b5-ac17-94bfefd5df72"
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

## Service Port

On every worker a service port is allocated for usage. This let's you for example to run
a webserver or any other daemon.

### Port

    print os.environ['SERVICE_PORT']

### IP

To know on which IP address the service is reachable, get the following variable:

    print os.environ['SERVICE_IP']

Use `SERVICE_IP6` for the IPv6 address.

### DNS

A host record is registered in a DNS zone in the form:

    USERNAME-BASENAME-INSTANCE_NUM[-V4,-V6].ZONE

IPv4 (A) and IPv6 (AAAA) record:

    print os.environ['SERVICE_DNS']

IPv4 only:

    print os.environ['SERVICE_DNS_V4']

IPv6 only:

    print os.environ['SERVICE_DNS_V6']

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

<a target="_blank" href="{% url 'django.swagger.base.view' %}#!/api">API Documentation</a>
