from setuptools import setup, find_packages

__VERSION__ = "0.1.6"


# http://stackoverflow.com/questions/14399534/how-can-i-reference-requirements-txt-for-the-install-requires-kwarg-in-setuptool
from pip.req import parse_requirements
install_reqs = parse_requirements("./requirements.txt")
reqs = [str(ir.req) for ir in install_reqs if not "github" in str(ir.url)]

setup(name='tumbo-server',
    version=__VERSION__,
    description='Reusable Django app for prototyping',
    long_description='django-fastapp is a reusable Django app which lets you prototype apps in the browser with client- and server-side elements.',
    url="https://github.com/fatrix/django-fastapp",
    author="Philip Sahli",
    author_email="philip@sahli.net",
    install_requires = reqs,
    packages = find_packages(),
    package_data = {'fastapp': ['fastapp/templates/*']},
    include_package_data=True,
    license ='MIT',
    #scripts=['cli/tumbo.py']
)
