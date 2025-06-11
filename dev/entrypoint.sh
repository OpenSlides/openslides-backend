#!/bin/bash

set -e

source scripts/export_database_variables.sh

printf "\nOpenslides Database:\n"
python cli/create_schema.py
printf "\n"
echo "enter entrypoint.sh"
meta/dev/scripts/wait-for-database.sh
echo "database is started"

# TODO: Re-add this code
# printf "\nMigrations:\n"
# python openslides_backend/migrations/migrate.py finalize
# printf "\n"

exec "$@"
