#!/bin/bash

set -e

source scripts/export_datastore_variables.sh
scripts/wait.sh $DATASTORE_WRITER_HOST $DATASTORE_WRITER_PORT

printf "\nOpenslides Database:\n"
python cli/create_schema.py
printf "\n"

# TODO: Re-add this code
# printf "\nMigrations:\n"
# python openslides_backend/migrations/migrate.py finalize
# printf "\n"

exec "$@"
