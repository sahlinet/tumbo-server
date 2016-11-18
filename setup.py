from setuptools import setup, find_packages
import glob
import os

__VERSION__ = "0.2.16"


# http://stackoverflow.com/questions/14399534/how-can-i-reference-requirements-txt-for-the-install-requires-kwarg-in-setuptool
from pip.req import parse_requirements
install_reqs = parse_requirements("./requirements.txt", session=False)
reqs = [str(ir.req) for ir in install_reqs if not "github" in str(ir.link)]

data_files = []
directories = glob.glob('compose-files/')
for directory in directories:
        files = glob.glob(directory+'*')
        data_files.append(("tumbo_server/"+directory, files))
        # then pass data_files to setup()
def package_files(*dirs):
    paths = {}
    #for (path, directories, filenames) in os.walk(directory):
    #    for filename in filenames:
    #        paths.append(os.path.join(path, filename))
    for src_dir in dirs:
        for root, dirs, files in os.walk(src_dir):
            #paths.append((root, map(lambda f:root + "/" + f, files)))
            paths.update({root: map(lambda f:root + "/" + f, files)})
            #paths.update({'': map(lambda f:root + "/" + f, files)})
    return paths

#data_files = package_files('tumbo/ui/templates')
print data_files
import sys
#sys.exit(0)

#version=__VERSION__+".1"
version="0.2.26"
print [('tumbo_server', data_files)]

setup(name='tumbo-server',
    version=version,
    description='Highly flexible Application Runtime Platform',
    long_description='Tumbo is a Server Platform for simplifying common development and deployment tasks. It conduce to go live quickly with an application - with less deployment- and configuration requirements.',
    url="https://tumbo.io",
    author="Philip Sahli",
    author_email="philip@sahli.net",
    license ='MIT',
    install_requires = reqs,
    packages = find_packages(),
    data_files = data_files,
    include_package_data=True,
    scripts=['cli/tumbo-cli.py'],
    zip_safe=False
)
