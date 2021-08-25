#!/bin/bash

export DATASTORE_DATABASE_HOST=${DATASTORE_DATABASE_HOST:-postgresql}
export DATASTORE_DATABASE_PORT=${DATASTORE_DATABASE_PORT:-5432}
export DATASTORE_DATABASE_USER=${DATASTORE_DATABASE_USER:-openslides}
export DATASTORE_DATABASE_NAME=${DATASTORE_DATABASE_NAME:-openslides}
export DATASTORE_DATABASE_PASSWORD=${DATASTORE_DATABASE_PASSWORD:-openslides}

printf "waiting for setup to finish\n"
wait-for-it -t 0 "${BACKEND_SETUP_HOST:-backend-setup}:${BACKEND_SETUP_PORT:-9002}"
printf "setup finished\n"

exec "$@"
