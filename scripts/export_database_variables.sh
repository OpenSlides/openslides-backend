#!/bin/bash

export DATABASE_HOST=${DATABASE_HOST:-postgres}
export DATABASE_PORT=${DATABASE_PORT:-5432}
export DATABASE_USER=${DATABASE_USER:-openslides}
export DATABASE_NAME=${DATABASE_NAME:-openslides}
export DATABASE_PASSWORD_FILE=${DATABASE_PASSWORD_FILE:-/run/secrets/postgres_password}
case $OPENSLIDES_DEVELOPMENT in
    1|on|On|ON|true|True|TRUE)  export PGPASSWORD="openslides";;
    *)                          export PGPASSWORD="$(cat "$DATABASE_PASSWORD_FILE")";;
esac
