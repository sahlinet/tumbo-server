FROM philipsahli/centos-v2:latest

RUN yum install -y postgresql-devel python-virtualenv libevent-devel gcc libffi-devel openssl-devel wget tar

RUN useradd -m -d /home/tumbo -s /bin/bash tumbo

WORKDIR /home/tumbo
RUN mkdir /home/tumbo/code/ && chown tumbo:tumbo code && mkdir /home/tumbo/logs && mkdir /logs && chown tumbo:tumbo /logs && mkdir /home/tumbo/.virtualenvs && mkdir /home/tumbo/.python-eggs && chown tumbo:tumbo /home/tumbo/.python-eggs

RUN virtualenv --no-site-packages /home/tumbo/.virtualenvs/tumbo

RUN rpm -iUvh http://yum.postgresql.org/9.3/redhat/rhel-7-x86_64/pgdg-centos93-9.3-1.noarch.rpm && yum -y install postgresql93

RUN /home/tumbo/.virtualenvs/tumbo/bin/pip install newrelic j2cli

# suds-jurko in django-plans need setuptools >=1.4
#RUN wget --no-check-certificate https://pypi.python.org/packages/source/s/setuptools/setuptools-1.4.2.tar.gz && tar -xvf setuptools-1.4.2.tar.gz
#RUN /home/tumbo/.virtualenvs/tumbo/bin/python setuptools-1.4.2/setup.py install
RUN /home/tumbo/.virtualenvs/tumbo/bin/pip install --upgrade setuptools==20.3.1

# nginx
RUN rpm -Uvh http://nginx.org/packages/centos/7/noarch/RPMS/nginx-release-centos-7-0.el7.ngx.noarch.rpm && yum -y install nginx && yum install -y epel-release && yum install -y moreutils pwgen


ADD tumbo /home/tumbo/code/tumbo
ADD example_bases /home/tumbo/code/examples
ADD app_worker /home/tumbo/code/app_worker
RUN cd /home/tumbo/code/tumbo && /home/tumbo/.virtualenvs/tumbo/bin/python setup.py install
# workaround because setup.py installs django-rest-framework as egg and django migrate fails with "Not a directory" when looking up for migrations instructions
RUN /home/tumbo/.virtualenvs/tumbo/bin/pip uninstall -y djangorestframework && /home/tumbo/.virtualenvs/tumbo/bin/pip install djangorestframework==2.4.3

RUN echo cachebust_14014248644
# WORKAROUND
RUN /home/tumbo/.virtualenvs/tumbo/bin/pip install -e git+https://github.com/rpalacios/django-sequence-field.git@f1bdc48c897e6cd95a3182f8253665609a87a895#egg=django_sequence_field-master
RUN /home/tumbo/.virtualenvs/tumbo/bin/pip install -e git+https://github.com/docker/docker-py.git@aa19d7b6609c6676e8258f6b900dea2eda1dbe95#egg=docker_py-master

# we need the fork sahlinet/swampdragon installed, because of reference in swampdragon-auth we need to install first our version.
#RUN /home/tumbo/.virtualenvs/tumbo/bin/pip install -e git+https://github.com/sahlinet/swampdragon.git@master#egg=swampdragon

ADD nginx.conf /etc/nginx/nginx.conf
ADD nginx_tumbo.conf /etc/nginx/conf.d/tumbo.conf
RUN rm /etc/nginx/conf.d/default.conf

RUN chown -R tumbo:tumbo /home/tumbo/.virtualenvs /home/tumbo/ /logs

ADD startup_app.sh /startup_app.sh
RUN mkdir /static && chown tumbo:tumbo /static && chmod 755 /startup_app.sh

# Not removing libffi-devel because ends in an error (install-info: No such file or directory for /usr/share/info/libffi.info.gz)
#RUN yum remove -y postgresql-devel libevent-devel gcc libffi-devel openssl-devel wget tar
RUN yum remove -y postgresql-devel libevent-devel gcc openssl-devel wget tar && yum clean all

EXPOSE 80
CMD ["/startup.sh"]
