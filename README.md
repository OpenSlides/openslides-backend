# OpenSlides Backend Service

Backend service for OpenSlides which

* accepts incomming requests to add, change or delete data, checks and parses them and writes them to the event stream,
* provides restricted data for a specific user,
* provides presentation of restricted data without autouodate,
* provides additional data for every autoupdate.

To setup development version run

    $ python -m venv .virtualenv
    $ source .virtualenv/bin/activate
    $ pip install --requirement requirements.txt

To start it run

    $ OPENSLIDES_BACKEND_DEBUG=1 python -m openslides_backend


## Environment variables

* OPENSLIDES_BACKEND_COMPONENT

  Use one of the following values to start only one component of this service: `actions` (listening on port 8000) or `restrictions` (listening on port 8001), `presenter` (listening on port 8002) or `addendum` (listening on port 8003). Defaults to all of them using different child processes. If using `all` you can shut down all compontes by sending SIGTERM to Python master process.

* OPENSLIDES_BACKEND_DEBUG

  Use a truthy value to set loglevel to debug and activate Gunicorn's reload mechanism. Default: 0

* OPENSLIDES_BACKEND_RUN_ALL_TESTS

  Use a truthy value to activate some more tests when running pytest. Default: 0

* OPENSLIDES_BACKEND_AUTHENTICATION_URL

  URL of authentication service. Default: http://localhost:9000/

* OPENSLIDES_BACKEND_PERMISSION_URL

  URL of permission service. Default: http://localhost:9001/

* OPENSLIDES_BACKEND_DATABASE_URL

  URL of database service. Default: http://localhost:9002/

* OPENSLIDES_BACKEND_EVENT_STORE_URL

  URL of event store service. Default: http://localhost:9003/
