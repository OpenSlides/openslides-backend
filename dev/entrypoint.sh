#!/bin/bash

set -e

export DATASTORE_DATABASE_HOST=${DATASTORE_DATABASE_HOST:-postgresql}
export DATASTORE_DATABASE_PORT=${DATASTORE_DATABASE_PORT:-5432}
export DATASTORE_DATABASE_USER=${DATASTORE_DATABASE_USER:-openslides}
export DATASTORE_DATABASE_NAME=${DATASTORE_DATABASE_NAME:-openslides}
export DATASTORE_DATABASE_PASSWORD=${DATASTORE_DATABASE_PASSWORD:-openslides}

dev/wait.sh $DATASTORE_WRITER_HOST $DATASTORE_WRITER_PORT

printf "\nMigrations:\n"
python migrations/migrate.py migrate
printf "\n"

exec "$@"
