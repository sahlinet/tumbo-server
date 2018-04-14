## Steps

### 1. Access Resource

The resource is wrapped by the function `cas_login`.

The client is passed to the inner function when:

* The user has a valid session.
* Base is marked as public.

Otherwise comes to 2.

See [code](aaa/cas/authentication.py)

### 2. Redirect to Login

Follow Redirect Response from 1. to CAS Login page with query parameter `service=...`

See [code](aaa/cas/authentication.py)

### 3. CAS Login

The client follows the Redirect Response and authenticates on the CAS Login page.

See [View code](aaa/cas/views.py#L26)

### 4. CAS Authentication

CAS authenticates the user against a configure backend.

### 5. CAS Response

On succesfull authentication CAS response with a Ticket for the user. The Ticket is transfered to the client as query parameter in a Redirect Response `Location` Header.

See [View code](aaa/cas/views.py#L67)

### 6. Ticket Transfer 

The client follows the Redirect Response and calls the Service with a Ticket as query parameter.

See [Wrapper function](aaa/cas/authentication.py#62)

### 7. Ticket Verification

CAS make a HTTP Call to the Ticket Service to verify if the ticket is valid for this service.

See [Wrapper function](aaa/cas/authentication.py#60)

#### 7.1 Verification

For the verification the view [aaa/cas/views.py#80](aaa/cas/views.py#80) is responsible to verify the ticket and response in case of a valid ticket with a JWT Token. 

#### 7.2 Authencation

Now the [Wrapper function](aaa/cas/authentication.py) queries the `User` object from database and calls `django.contrib.auth.login` to create a session.

#### 7.3 Response

> Now comes the tricky part because the Session must be restricted to `/userland....`. But Django supports only one configuration. See [SESSION_COOKIE_PATH](https://docs.djangoproject.com/en/2.0/ref/settings/#std:setting-SESSION_COOKIE_PATH)

With the following code we are able to create a new Session Key. The custom Cookie-Path is set the the session, so we can later process the response and overwrite Django's default behaviour.

    request.session['cookie_path'] = "/userland/%s/%s" % (
                base.user.username, base.name)
    request.session.cycle_key()

#### 7.4 Middleware

The default behaviour in Django's `django.contrib.sessions.middleware.SessionMiddleware` (to set as Cookie-Path the path from `settings.SESSION_COOKIE_PATH`) is changed by adding a Middleware, which sets the path from the session's `cookie_path` object.


See [CasSessionMiddleware](aaa/cas/middleware.py)

### 8. Return with Session

In 7. Ticket Verification the client received a HTTP Response with a `Set-Cookie` Header with the session.

### 9. Use Service

In 8. the response was a Redirect Response and the client can now use the service with the session (he is authentication).





