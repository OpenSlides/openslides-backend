#!/bin/bash

export DATASTORE_DATABASE_HOST=${DATASTORE_DATABASE_HOST:-postgresql}
export DATASTORE_DATABASE_PORT=${DATASTORE_DATABASE_PORT:-5432}
export DATASTORE_DATABASE_USER=${DATASTORE_DATABASE_USER:-openslides}
export DATASTORE_DATABASE_NAME=${DATASTORE_DATABASE_NAME:-openslides}
export DATASTORE_DATABASE_PASSWORD=${DATASTORE_DATABASE_PASSWORD:-openslides}

./wait.sh $DATASTORE_WRITER_HOST $DATASTORE_WRITER_PORT

if [ -f mig-mark/MARK ]; then
  printf "\nMARK found skipping Migrations\n"
else
  printf "\nMigrations:\n"
  touch mig-mark/MARK
  python migrations/migrate.py migrate
  rm mig-mark/MARK
  printf "\n"
fi

exec "$@"
