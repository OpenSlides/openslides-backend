# OpenSlides backend service

Backend service for OpenSlides which accepts incomming requests to add, change
or delete data, checks and parses them and writes them to the event stream.

It is also responsible for ...

To setup development version run

    $ python -m venv .virtualenv
    $ source .virtualenv/bin/activate
    $ pip install --upgrade pip
    $ pip install --requirement requirements.txt

To start it run

    $ python start.py  # Stars Werkzeug's development server

or

    $ OPENSLIDES_BACKEND_DEBUG=1 gunicorn --config=python:gunicorn_conf openslides_backend.wsgi:application
