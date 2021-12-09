#!/bin/bash

source wait.sh

if [[ -f /datastore-service/scripts/system/create_schema.sh ]]; then
    pushd /datastore-service/
    export PGPASSWORD="$DATASTORE_DATABASE_PASSWORD"
    scripts/system/create_schema.sh
    popd
fi

exec "$@"
