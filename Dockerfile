FROM philipsahli/pyas:latest

RUN echo "tumbo ALL=(ALL)       NOPASSWD: ALL" >> /etc/sudoers && sed -i -e 's/Defaults    requiretty.*/ #Defaults    requiretty/g' /etc/sudoers

ENV PIP /home/tumbo/.virtualenvs/tumbo/bin/pip
ENV CODE_DIR /home/tumbo/code
ENV HOME /home/tumbo

RUN useradd -m -d $HOME -s /bin/bash tumbo

WORKDIR $HOME
RUN mkdir $CODE_DIR && chown tumbo:tumbo code && mkdir $HOME/.virtualenvs && mkdir $HOME/.python-eggs && chown tumbo:tumbo $HOME/.python-eggs

RUN virtualenv -p /usr/local/bin/python --no-site-packages $HOME/.virtualenvs/tumbo


RUN rpm -iUvh http://yum.postgresql.org/9.3/redhat/rhel-7-x86_64/pgdg-centos93-9.3-3.noarch.rpm && yum -y install postgresql93


RUN $PIP install newrelic j2cli

RUN echo cachebust_1470943960

ADD dist $CODE_DIR/dist
ADD examples $CODE_DIR/examples
RUN $PIP install --upgrade pip && cd $CODE_DIR/dist && $PIP install tumbo-server-*.tar.gz

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
RUN yum clean all

EXPOSE 80
USER tumbo

CMD ["/startup.sh"]
