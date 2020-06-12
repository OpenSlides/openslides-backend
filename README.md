# OpenSlides Backend Service

Backend service for OpenSlides which

* accepts incomming requests to add, change or delete data, checks and parses them and writes them to the event stream,
* provides presentation of restricted data without autoupdate,
* provides additional data for every autoupdate (TODO).

To setup development version run

    $ python -m venv .virtualenv
    $ source .virtualenv/bin/activate
    $ pip install --requirement requirements.txt

To start it run

    $ OPENSLIDES_BACKEND_DEBUG=1 python -m openslides_backend

or

    $ make run-debug

## Listening ports

The actions component listens to port 9002. The presenter component listens to port 9003. Both listen to all devices (0.0.0.0).


## Environment variables

* OPENSLIDES_BACKEND_COMPONENT

  Use one of the following values to start only one component of this service: `actions` or `presenter` or `addendum`. Defaults to all of them using different child processes. If using `all` you can shut down all compontes by sending SIGTERM to Python master process.

* OPENSLIDES_BACKEND_DEBUG

  Use a truthy value to set loglevel to debug and activate Gunicorn's reload mechanism. Default: 0

* OPENSLIDES_BACKEND_RUN_ALL_TESTS

  Use a truthy value to activate some more tests when running pytest. Default: 0

* AUTHENTICATION_URL

  URL of authentication service. Default: http://localhost:9004/

* PERMISSION_URL

  URL of permission service. Default: http://localhost:9005/

* DATASTORE_READER_URL

  URL of datastore reader service. Default: http://localhost:9010/internal/reader

* DATASTORE_WRITER_URL

  URL of datastore writer service. Default: http://localhost:9011/internal/writer

* OPENSLIDES_BACKEND_WORKER_TIMEOUT

  Gunicorn worker timeout in seconds. Default: 30


# Some curl examples

You may run curl against this service like this:

    $ curl localhost:9002/health
    $ curl localhost:9002 -X POST -H "Content-Type: application/json" -d '[{"action": "topic.create", "data": [{"meeting_id": 1, "title": "foo"}]}]'
    $ curl localhost:9002 -X POST -H "Content-Type: application/json" -d '[{"action": "topic.update", "data": [{"id": 1, "title": "bar"}]}]'

    $ curl localhost:9003/health
    $ curl localhost:9003 -X GET -H "Content-Type:application/json" -d '[{"presenter": "whoami"}]' localhost:9003
