#!/bin/bash
set -e

export MEDIA_DATABASE_HOST=${MEDIA_DATABASE_HOST:-postgres}
export MEDIA_DATABASE_PORT=${MEDIA_DATABASE_PORT:-5432}
export MEDIA_DATABASE_NAME=${MEDIA_DATABASE_NAME:-mediafiledata}
export MEDIA_DATABASE_USER=${MEDIA_DATABASE_USER:-openslides}
export MEDIA_DATABASE_PASSWORD_FILE=${MEDIA_DATABASE_PASSWORD_FILE:-/run/secrets/postgres_password}
case $OPENSLIDES_DEVELOPMENT in
    1|on|On|ON|true|True|TRUE)  export PGPASSWORD="openslides";;
    *)                          export PGPASSWORD="$(cat "$MEDIA_DATABASE_PASSWORD_FILE")";;
esac
