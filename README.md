# OpenSlides backend service

Backend service for OpenSlides which accepts incomming requests to add, change or delete data, checks and parses them and writes them to the event stream.

It is also responsible for ...

To setup run

    $ python -m venv .virtualenv
    $ source .virtualenv/bin/activate
    $ pip install --upgrade pip
    $ pip install --requirement requirements.txt

To start run

    $ python start.py

or

    $ gunicorn --config=python:gunicorn_conf openslides_write_service.wsgi:application
