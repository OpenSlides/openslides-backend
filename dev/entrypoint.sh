#!/bin/bash

set -e

source scripts/export_datastore_variables.sh
scripts/wait.sh $DATASTORE_WRITER_HOST $DATASTORE_WRITER_PORT

printf "\nMigrations:\n"
python openslides_backend/migrations/migrate.py finalize
printf "\n"

global/meta/dev/scripts/apply_db_schema.sh

exec "$@"
