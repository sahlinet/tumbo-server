FROM philipsahli/centos:latest

RUN yum install -y postgresql-devel python-virtualenv libevent-devel gcc libffi-devel openssl-devel wget tar sudo

RUN echo "tumbo ALL=(ALL)       NOPASSWD: ALL" >> /etc/sudoers
RUN sed -i -e 's/Defaults    requiretty.*/ #Defaults    requiretty/g' /etc/sudoers

ENV PIP /home/tumbo/.virtualenvs/tumbo/bin/pip
ENV CODE_DIR /home/tumbo/code
ENV HOME /home/tumbo

RUN useradd -m -d $HOME -s /bin/bash tumbo

WORKDIR $HOME
RUN mkdir $CODE_DIR && chown tumbo:tumbo code && mkdir $HOME/.virtualenvs && mkdir $HOME/.python-eggs && chown tumbo:tumbo $HOME/.python-eggs

RUN virtualenv --no-site-packages $HOME/.virtualenvs/tumbo

RUN rpm -iUvh http://yum.postgresql.org/9.3/redhat/rhel-7-x86_64/pgdg-centos93-9.3-3.noarch.rpm && yum -y install postgresql93


RUN $PIP install newrelic j2cli

# suds-jurko in django-plans need setuptools >=1.4
#RUN wget --no-check-certificate https://pypi.python.org/packages/source/s/setuptools/setuptools-1.4.2.tar.gz && tar -xvf setuptools-1.4.2.tar.gz
#RUN /home/tumbo/.virtualenvs/tumbo/bin/python setuptools-1.4.2/setup.py install
RUN $PIP install --upgrade setuptools==20.3.1

# nginx
RUN yum install -y yum-utils
RUN yum-config-manager --save --setopt=epel.skip_if_unavailable=true
RUN rpm -ivh https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm && yum -y install -y epel-release && yum install -y moreutils pwgen
RUN rpm -Uvh http://nginx.org/packages/centos/7/noarch/RPMS/nginx-release-centos-7-0.el7.ngx.noarch.rpm && yum -y install nginx 


ADD dist $CODE_DIR/dist
ADD examples $CODE_DIR/examples
#ADD worker $CODE_DIR/worker
RUN ls -al $CODE_DIR
RUN $PIP install --upgrade pip
RUN cd $CODE_DIR/dist && $PIP install tumbo-server --find-links=.
# workaround because setup.py installs django-rest-framework as egg and django migrate fails with "Not a directory" when looking up for migrations instructions
#RUN $PIP uninstall -y djangorestframework && $PIP install djangorestframework==2.4.3

RUN echo cachebust_1470943960
# WORKAROUND
RUN $PIP install -e git+https://github.com/rpalacios/django-sequence-field.git@f1bdc48c897e6cd95a3182f8253665609a87a895#egg=django_sequence_field-master
RUN $PIP install -e git+https://github.com/docker/docker-py.git@aa19d7b6609c6676e8258f6b900dea2eda1dbe95#egg=docker_py-master

ADD conf/nginx.conf /etc/nginx/nginx.conf
ADD conf/nginx_tumbo.conf /etc/nginx/conf.d/tumbo.conf
RUN rm /etc/nginx/conf.d/default.conf

RUN chown -R tumbo:tumbo $HOME/.virtualenvs $HOME/

ADD bin/startup_app.sh /startup_app.sh
RUN mkdir /static && chown tumbo:tumbo /static && chmod 755 /startup_app.sh

# Not removing libffi-devel because ends in an error (install-info: No such file or directory for /usr/share/info/libffi.info.gz)
#RUN yum remove -y postgresql-devel libevent-devel gcc libffi-devel openssl-devel wget tar
RUN yum remove -y postgresql-devel libevent-devel gcc openssl-devel wget tar && yum clean all

EXPOSE 80
USER tumbo

CMD ["/startup.sh"]
