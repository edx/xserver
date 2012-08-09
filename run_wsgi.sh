#!/usr/bin/env bash
gunicorn -w 4 -b 127.0.0.1:3031 pyxserver_wsgi:application &
