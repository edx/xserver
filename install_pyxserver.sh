#!/usr/bin/env bash

# Install requirements
apt-get update
apt-get install nginx gunicorn
apt-get install gcc
apt-get install libxml2-dev libxslt1-dev python-dev python-lxml python-pip
pip install requests

# Setup nginx proxy, then restart
cp nginx.conf /etc/nginx/nginx.conf
/etc/init.d/nginx restart

# Run pyxserver
./run_wsgi.sh
