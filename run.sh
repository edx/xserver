gunicorn --preload -b 127.0.0.1:3031 --timeout=35 --pythonpath=. pyxserver_wsgi:application
