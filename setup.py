import glob
import os

# http://stackoverflow.com/questions/14399534/how-can-i-reference-requirements-txt-for-the-install-requires-kwarg-in-setuptool
from pip.req import parse_requirements
from setuptools import find_packages, setup

__VERSION__ = "0.5.27-dev"


install_reqs = parse_requirements("./requirements.txt", session=False)
reqs = [str(ir.req) for ir in install_reqs if not "github" in str(ir.link)]

data_files = []
directories = glob.glob('compose-files/')
for directory in directories:
        files = glob.glob(directory+'*')
        data_files.append(("tumbo_server/"+directory, files))
directories = glob.glob('k8s-files/cli/')
for directory in directories:
        files = glob.glob(directory+'*')
        data_files.append(("tumbo_server/"+directory, files))



setup(name='tumbo-server',
    version=__VERSION__,
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
