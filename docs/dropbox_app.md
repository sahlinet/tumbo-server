https://www.dropbox.com/developers/apps -> "Create app"


"Create a new app on the Dropbox Platform"



What type of app do you want to create? -> Dropbox API app
Can your app be limited to its own folder? -> Yes My app only needs access to files it creates.
Provide an app name, and you're on your way. -> planet lite test

1. Choose an API

2. Choose the type of access you need

3. Name your app

Then on the "Settings" tab

Note "App key" and "App secret"

OAuth 2 -> Redirect URI's

    https://tumbo.sahli.net/fastapp/dropbox_auth_finish/

Webhooks -> Webhook URI's

    https://tumbo.sahli.net/fastapp/dropbox_notify/

    - DROPBOX_CONSUMER_KEY
    - DROPBOX_CONSUMER_SECRET
    - DROPBOX_REDIRECT_URL
