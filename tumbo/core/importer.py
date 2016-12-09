import logging

from distutils.util import strtobool
from configobj import ConfigObj

from core.models import Base, Setting, Apy
from core.utils import Connection

logger = logging.getLogger(__name__)

def _read_config(app_config):
    appconfig = ConfigObj(app_config)
    return appconfig

def _handle_settings(settings, base_obj, override_public=False, override_private=False):
    """
    dict with settings (k, v)
    """
    # get settings
    print settings.items()
    for k, v in settings.items():
        setting_obj, created = Setting.objects.get_or_create(base=base_obj, key=k)
        # set if empty
        if not setting_obj.value:
            setting_obj.value = v['value']
        # override_public
        if setting_obj.public and override_public:
            setting_obj.value = v['value']
        # override_private
        if not setting_obj.public and override_private:
            setting_obj.value = v['value']
        setting_obj.public = strtobool(v['public'])
        setting_obj.save()

def _handle_apy(filename, content, base_obj, appconfig):
    name = filename.replace(".py", "")
    apy, created = Apy.objects.get_or_create(base=base_obj, name=name)
    apy.module = content
    description = appconfig['modules'][name]['description']
    if description:
        apy.description = description
    public = appconfig['modules'][name].get('public', None)
    if public:
        apy.public = strtobool(public)
    apy.save()


def import_base(zf, user_obj, name, override_public, override_private):
    base, created = Base.objects.get_or_create(user=user_obj, name=name)
    if not created:
        logger.info("base '%s' did already exist" % name)
        base.save()
    # Dropbox connection
    try:
        dropbox_connection = Connection(base.auth_token)
    except Exception, e:
        logger.exception("Error on Connectin to Dropbx")

    # app.config
    print zf.open("app.config")
    appconfig = _read_config(zf.open("app.config"))

    # Apy
    for apy in appconfig['modules'].keys():
        filename = apy+".py"
        apy_content = zf.open(filename).read()
        _handle_apy(filename, apy_content, base, appconfig)

    # settings
    settings = appconfig['settings']
    _handle_settings(settings, base)

    filelist = zf.namelist()
    for filename in filelist:
        # ignore files starting with '__'
        if filename.startswith('__'):
            continue

        # static
        logger.info("staticfile: "+filename)
        content = zf.open(filename).read()
        if filename == "index.html":
            base.content = content
            base.save()

        if "static" in filename:
            file = "/%s/%s" % (base.name, filename)
            dropbox_connection.put_file(file, content)

    return base
