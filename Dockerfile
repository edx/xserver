FROM ubuntu:xenial as openedx

RUN apt update && \
  apt install -y git-core language-pack-en apparmor apparmor-utils python python-pip python-dev build-essential gcc gfortran liblapack-dev libxml++2.6-dev libxml2-dev libxml2-utils libxslt1-dev python-dev apparmor-utils -qy && \
  pip install --upgrade pip setuptools && \
  rm -rf /var/lib/apt/lists/*

RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

WORKDIR /edx/app/xserver
COPY requirements /edx/app/xserver/requirements
RUN pip install -r requirements/base.txt

EXPOSE 8050

USER app
RUN useradd -m --shell /bin/false app
CMD gunicorn -c /edx/app/docker_gunicorn_config.py --bind=0.0.0.0:8050 --workers 2 --max-requests=1000 pyxserver_wsgi:application

COPY . /edx/app/xserver

FROM openedx as edx.org
RUN pip install newrelic
CMD newrelic-admin run-program gunicorn -c /edx/app/docker_gunicorn_config.py --bind=0.0.0.0:8050 --workers 2 --max-requests=1000 pyxserver_wsgi:application
