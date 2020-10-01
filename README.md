# OpenSlides Backend Service

Backend service for OpenSlides which

* accepts incomming requests to add, change or delete data, checks and parses them and writes them to the datastore,
* provides presentation of restricted data without autoupdate,

Use docker to build and start the application with your favorite tools. See [Dockerfile](Dockerfile) for steps to setup the production build.


## Development

### Development with Docker Compose

To start the development build run in a first terminal

    $ make start-dev-interactive

Then run in a separate terminal

    $ make run-dev-standalone

Inside this terminal you may use some commands you find in the [Makefile](Makefile). You may want to use

    $ make run-debug
    $ make test
    $ make  # Coding style tools, typechecker and tests all together

You may also use

    $ make run-dev

to do everything at once. Do not forget to run

    $ make stop-dev
  
when you are done.

### Development without Docker Compose

You may use some commands you find in the [Makefile](Makefile) even outside a docker environment. Nevertheless we prefer some kind of system tests here that require other services of Openslides 4 (e. g. the datastore with postgres and redis). If you do not use Docker Compose, you have to provide these services in another way. Only for integration and unit tests all other services can be absent.

To setup and local development version run

    $ python -m venv .virtualenv
    $ source .virtualenv/bin/activate
    $ pip install --requirement dev/requirements_development.txt

To start it run

    $ make run-debug

### Generate models file

To generate a new models.py file (updated in [OpenSlides Main Repository](https://github.com/OpenSlides/OpenSlides)) run

    $ make generate-models


## Listening ports

The action component listens to port 9002. The presenter component listens to port 9003. Both listen to all devices (0.0.0.0).


## Environment variables

* OPENSLIDES_BACKEND_COMPONENT

  Use one of the following values to start only one component of this service: `action` or `presenter`. Defaults to all of them using different child processes. If using `all` you can shut down all compontes by sending SIGTERM to Python master process.

* OPENSLIDES_BACKEND_DEBUG

  Use a truthy value to set loglevel to debug and activate Gunicorn's reload mechanism. Default: 0

* AUTH_PROTOCOL

  Protocol of authentication service. Default: http

* AUTH_HOST

  Host of authentication service. Default: localhost

* AUTH_PORT

  Port of authentication service. Default: 9004

* AUTH_PATH

  Path of authentication service. Default is an empty string.

* PERMISSION_PROTOCOL

  Protocol of permission service. Default: http

* PERMISSION_HOST

  Host of permission service. Default: localhost

* PERMISSION_PORT

  Port of permission service. Default: 9005

* PERMISSION_PATH

  Path of permission service. Default is an empty string.

* DATASTORE_READER_PROTOCOL

  Protocol of datastore reader service. Default: http

* DATASTORE_READER_HOST

  Host of datastore reader service. Default: localhost

* DATASTORE_READER_PORT

  Port of datastore reader service. Default: 9010

* DATASTORE_READER_PATH

  Path of datastore reader service. Default: /internal/datastore/reader

* DATASTORE_WRITER_PROTOCOL

  Protocol of datastore writer service. Default: http

* DATASTORE_WRITER_HOST

  Host of datastore writer service. Default: localhost

* DATASTORE_WRITER_PORT

  Port of datastore writer service. Default: 9011

* DATASTORE_WRITER_PATH

  Path of datastore writer service. Default: /internal/datastore/writer

* OPENSLIDES_BACKEND_WORKER_TIMEOUT

  Gunicorn worker timeout in seconds. Default: 30


# Some curl examples

You may run curl against this service like this:

    $ curl localhost:9002/health
    $ curl localhost:9002 -X POST -H "Content-Type: application/json" -d '[{"action": "topic.create", "data": [{"meeting_id": 1, "title": "foo"}]}]'
    $ curl localhost:9002 -X POST -H "Content-Type: application/json" -d '[{"action": "topic.update", "data": [{"id": 1, "title": "bar"}]}]'

    $ curl localhost:9003/health
    $ curl localhost:9003 -X GET -H "Content-Type:application/json" -d '[{"presenter": "whoami"}]'

The action health path returns a list of all possible actions with its JSON schema.
