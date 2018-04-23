import logging
from distutils.util import strtobool

from configobj import ConfigObj

from core.models import Apy, Base, Setting
from core.utils import Connection
from core.storage import Storage

logger = logging.getLogger(__name__)


def _read_config(app_config):
    appconfig = ConfigObj(app_config)
    return appconfig


def _handle_settings(settings, base_obj, override_public=False, override_private=False):
    """
    dict with settings (k, v)
    """
    # get settings
    for k, v in settings.items():
        setting_obj, _ = Setting.objects.get_or_create(
            base=base_obj, key=k)
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
    apy, _ = Apy.objects.get_or_create(base=base_obj, name=name)
    apy.module = content
    description = appconfig['modules'][name]['description']
    if description:
        apy.description = description
    schedule = appconfig['modules'][name]['schedule']
    if schedule:
        apy.schedule = appconfig['modules'][name]['schedule']
    else:
        apy.schedule = ""
    public = appconfig['modules'][name].get('public', None)
    if public:
        apy.public = strtobool(public)
    apy.save()


def import_base(zf, user_obj, name, override_public, override_private):
    base, created = Base.objects.get_or_create(user=user_obj, name=name)
    if not created:
        logger.info("base '%s' did already exist" % name)
        base.save()

    storage = Storage.factory()(base)
    # app.config
    appconfig = _read_config(zf.open("app.config"))

    # Apy
    for apy in appconfig['modules'].keys():
        filename = apy+".py"
        apy_content = zf.open(filename).read()
        _handle_apy(filename, apy_content, base, appconfig)

    # Access
    access = appconfig.get('access', None)
    if access:
        base.static_public = strtobool(access['static_public'])
        base.public = strtobool(access['public'])

    # Settings
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
            sfile = "%s/%s" % (base.name, filename)
            storage.put(sfile, content)

    return base
