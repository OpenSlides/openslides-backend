# OpenSlides Backend Service

Backend service for OpenSlides which

* accepts incomming requests to add, change or delete data, checks and parses them and writes them to the datastore,
* provides presentation of restricted data without autoupdate,

Use docker to build and start the application with your favorite tools. See [Dockerfile](Dockerfile) for steps to setup the production build.


## Development

### Development with Docker Compose

The setup is structured to do all development inside the docker containers. To start everything at once and get entered into a bash shell, run 

    $ make run-dev

All containers can be stopped afterwards by running

    $ make stop-dev

You can also start the components manually. To do that, run

    $ make start-dev-interactive

Then run in a separate terminal

    $ make run-dev-attach

Inside this terminal you may use some commands you find in the [Makefile](Makefile). You may want to use

    $ make run-debug
    $ make test
    $ make  # Coding style tools, typechecker and tests all together

### Generate models file

To generate a new models.py file (updated in [OpenSlides Main Repository](https://github.com/OpenSlides/OpenSlides)) run (inside the docker container)

    $ make generate-models

If you do not want to generate from the current master, you can provide either a local path or an URL via the variable `MODELS_PATH`. This way, you can generate only partial changes if multiple changes to the models file were merged into the master:

    $ MODEL_PATH="https://raw.githubusercontent.com/OpenSlides/OpenSlides/0e56d1360e45f1ca3ef3dc004b87a8e23829c45b/docs/models.yml" make generate-models

Note that you need to provide the raw file if you want to use a GitHub link.

### Development without Docker Compose

It is highly encouraged to use docker for development purposes, since all requirements etc. are already fulfilled there. You may use some commands you find in the [Makefile](Makefile) even outside a docker environment. Nevertheless we prefer some kind of system tests here that require other services of Openslides 4 (e. g. the datastore with postgres and redis). If you do not use Docker Compose, you have to provide these services in another way. Only for integration and unit tests all other services can be absent.

To setup and local development version run

    $ python -m venv .virtualenv
    $ source .virtualenv/bin/activate
    $ pip install --requirement dev/requirements_development.txt

To start it run

    $ make run-debug

## Listening ports

The action component listens to port 9002. The presenter component listens to port 9003. Both listen to all devices (0.0.0.0).


## Environment variables

* OPENSLIDES_BACKEND_COMPONENT

  Use one of the following values to start only one component of this service: `action` or `presenter`. Defaults to all of them using different child processes. If using `all` you can shut down all compontes by sending SIGTERM to Python master process.

* OPENSLIDES_DEVELOPMENT

  Set this variable e. g. to 1 to set loglevel to debug and activate Gunicorn's reload mechanism.

* OPENSLIDES_BACKEND_RAISE_4XX

  Set this variable to raise HTTP 400 and 403 as exceptions instead of valid HTTP responses.

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

* AUTH_HOST and AUTH_PORT

  Implicitly used by the authlib to get the endpoint for the auth-service

# Some curl examples

You may run curl against this service like this:

    $ curl localhost:9002/health
    $ curl localhost:9002 -X POST -H "Content-Type: application/json" -d '[{"action": "topic.create", "data": [{"meeting_id": 1, "title": "foo"}]}]'
    $ curl localhost:9002 -X POST -H "Content-Type: application/json" -d '[{"action": "topic.update", "data": [{"id": 1, "title": "bar"}]}]'

    $ curl localhost:9003/health
    $ curl localhost:9003 -X GET -H "Content-Type:application/json" -d '[{"presenter": "whoami"}]'

The action health path returns a list of all possible actions with its JSON schema.
