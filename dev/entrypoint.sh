#!/bin/bash

set -e

source scripts/export_datastore_variables.sh
scripts/wait.sh $DATASTORE_WRITER_HOST $DATASTORE_WRITER_PORT

printf "\nOpenslides Database:\n"
python cli/create_schema.py
printf "\n"

# printf "\nMigrations:\n"
# python openslides_backend/migrations/migrate.py finalize
# printf "\n"

exec "$@"

# TODO: Fix this script
