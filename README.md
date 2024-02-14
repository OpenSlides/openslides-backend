# OpenSlides Backend Service

Backend service for OpenSlides which

* accepts incomming requests to add, change or delete data, checks and parses them and writes them to the datastore,
* provides presentation of restricted data without autoupdate,

Use docker to build and start the application with your favorite tools. See [Dockerfile](Dockerfile) for steps to setup the production build.

## Translations

We recently updated the source language in the database from english to the user's language. To migrate your data from english to your preferred language, use the provided [translation script](cli/translate.py).

## Development

Documentation for the actions: [Action overview](docs/Actions-Overview.md)
Documentation for the presenters: [Presenter overview](docs/Presenter-Overview.md)

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
    $ make all # Coding style tools, typechecker and tests all together
    $ make check-all # Checks for consistence of models.yml and *.py, initial-data and permissions

### Generate models file

To generate a new models.py file run (inside the docker container)

    $ make generate-models

The original models.yml is now included in this repository at global/meta/. If you do not want to generate from the current backend, you can provide either a local path or an URL via the variable `MODELS_PATH`. This way, you can generate only partial changes if multiple changes to the models file were merged into the main:

    $ MODEL_PATH="local path or GitHub link" make generate-models

Note that you need to provide the raw file if you want to use a GitHub link.

### Development without Docker Compose

It is highly encouraged to use docker for development purposes, since all requirements etc. are already fulfilled there. You may use some commands you find in the [Makefile](Makefile) even outside a docker environment. Nevertheless we prefer some kind of system tests here that require other services of Openslides 4 (e. g. the datastore with postgres and redis). If you do not use Docker Compose, you have to provide these services in another way. Only for integration and unit tests all other services can be absent.

To setup and local development version run

    $ python -m venv .virtualenv
    $ source .virtualenv/bin/activate
    $ . requirements/export_service_commits.sh && pip install --requirement requirements/requirements_development.txt

To start it run

    $ make run-debug

## Listening ports

The action component listens to port 9002. The presenter component listens to port 9003. Both listen to all devices (0.0.0.0).


## Environment variables

### Functionality

* `OPENSLIDES_BACKEND_COMPONENT`

  Use one of the following values to start only one component of this service: `action` or `presenter`. Defaults to all of them using different child processes. If using `all` you can shut down all compontes by sending SIGTERM to Python master process.

* `ACTION_PORT`

  Action component listens on this port. Default: `9002`

* `PRESENTER_PORT`

  Presenter component listens on this port. Default `9003`

* `OPENTELEMETRY_ENABLED`

  Set this variable e. g. to `1` to enable span reporting to an OpenTelemetry collector (defined in the main OpenSlides repository).

* `OPENSLIDES_LOGLEVEL`

  In production mode you can set the loglevel to `debug`, `info`, `warning`, `error` or `critical`. Default is `info`.

* `OPENSLIDES_BACKEND_NUM_WORKERS`

  Number of Gunicorn workers. Default: `1`

* `OPENSLIDES_BACKEND_WORKER_TIMEOUT`

  Gunicorn worker timeout in seconds. Default: `30`

* `OPENSLIDES_BACKEND_THREAD_WATCH_TIMEOUT`

  Seconds after which an action is delegated to an action worker. `-1` represents an infinite timeout. `-2` deactivates action workers and local threading alltogether. Default: `1`

### Development

* `OPENSLIDES_DEVELOPMENT`

  Set this variable e. g. to `1` to set loglevel to `debug` and activate Gunicorn's reload mechanism.

* `OPENSLIDES_BACKEND_RAISE_4XX`

  Set this variable to raise HTTP 400 and 403 as exceptions instead of valid HTTP responses.

### Connection to other services
* `DATASTORE_READER_PROTOCOL`

  Protocol of datastore reader service. Default: `http`

* `DATASTORE_READER_HOST`

  Host of datastore reader service. Default: `localhost`

* `DATASTORE_READER_PORT`

  Port of datastore reader service. Default: `9010`

* `DATASTORE_READER_PATH`

  Path of datastore reader service. Default: `/internal/datastore/reader`

* `DATASTORE_WRITER_PROTOCOL`

  Protocol of datastore writer service. Default: `http`

* `DATASTORE_WRITER_HOST`

  Host of datastore writer service. Default: `localhost`

* `DATASTORE_WRITER_PORT`

  Port of datastore writer service. Default: `9011`

* `DATASTORE_WRITER_PATH`

  Path of datastore writer service. Default: `/internal/datastore/writer`

* `AUTH_HOST`

  Host of auth service. Used by the `authlib` package. Default: `localhost`

* `AUTH_PORT`

  Port of auth service. Used by the `authlib` package. Default: `9004`


# Some curl examples

You may run curl against this service like this:

    $ curl localhost:9002/system/action/health
    $ curl localhost:9002/system/action/info
    $ curl localhost:9002/system/action/handle_request -X POST -H "Content-Type: application/json" -d '[{"action": "topic.create", "data": [{"meeting_id": 1, "title": "foo"}]}]'
    $ curl localhost:9002/system/action/handle_request -X POST -H "Content-Type: application/json" -d '[{"action": "topic.update", "data": [{"id": 1, "title": "bar"}]}]'

    $ curl localhost:9003/system/presenter/health
    $ curl localhost:9003/system/presenter/handle_request -X GET -H "Content-Type:application/json" -d '[{"presenter": "whoami"}]'

The action health path returns a list of all possible actions with its JSON schema.

## Available routes

General schema for public routes: `/system/<service>/<route>`
General schema for internal routes: `/internal/<route>`

### Action Service

* `/system/action/handle_request`: Main route of the service, is used to execute actions.
* `/system/action/handle_separately`: Same function as `handle_request`, but the request is not executed atomically,
  meaning each action is executed and the result sent to the datastore separately.
* `/internal/handle_request`: Same as the first route, but only for internal usage: All permission checks are skipped
  and created write requests will have id -1.
* `/system/action/health`: Return `{"status": "running"}` if successful. Useful for status checks against the backend.
* `/system/action/info`: Returns a list of all possible actions with their respective JSON schema.
* `/internal/migrations`: Provides remote access to the migration tool. For more information, take a look at the [migration route docs](/docs/migration_route.md)

### Presenter Service

* `/system/presenter/handle_request`: Main route of the service, is used to fetch presenter results.
* `/system/presenter/health`: Return `{"status": "running"}` if successful. Useful for status checks against the backend.
