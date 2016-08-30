def get_setting(setting):
    return getattr(settings, setting)

INSTALLED_APPS = get_setting('INSTALLED_APPS') + (
    'social.apps.django_app.default',
)

AUTHENTICATION_BACKENDS = (
    'social.backends.github.GithubOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

TEMPLATE_CONTEXT_PROCESSORS += (
    'social.apps.django_app.context_processors.backends',
    'social.apps.django_app.context_processors.login_redirect',
)

SOCIAL_AUTH_GITHUB_KEY = '367fc54a95e4953e6ee9'
SOCIAL_AUTH_GITHUB_SECRET = '35949713f8ef99eb4a1183c67474440df5907335'
LOGIN_REDIRECT_URL = '/profile/'

SOCIAL_AUTH_PIPELINE = (
    'social.pipeline.social_auth.social_details',
    'social.pipeline.social_auth.social_uid',
    'social.pipeline.social_auth.auth_allowed',
    'social.pipeline.social_auth.social_user',
    'social.pipeline.user.get_username',
    'social.pipeline.user.create_user',
    'aaa.pipeline.restrict_user',
    'social.pipeline.social_auth.associate_user',
    'social.pipeline.social_auth.load_extra_data',
    'social.pipeline.user.user_details',
)

RESTRICTED_TO_USERS = os.environ.get("RESTRICTED_TO_USERS", "").split(",")
