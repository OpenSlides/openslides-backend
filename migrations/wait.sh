#!/bin/bash

export MESSAGE_BUS_HOST=${MESSAGE_BUS_HOST:-redis}
export MESSAGE_BUS_PORT=${MESSAGE_BUS_PORT:-6379}

wait-for-it -t 0 "$MESSAGE_BUS_HOST:$MESSAGE_BUS_PORT"

source /util/scripts/export_datastore_variables.sh

until pg_isready -h "$DATASTORE_DATABASE_HOST" -p "$DATASTORE_DATABASE_PORT" -U "$DATASTORE_DATABASE_USER"; do
    echo "Waiting for Postgres server '$DATASTORE_DATABASE_HOST' to become available..."
    sleep 3
done
