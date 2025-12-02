#!/bin/bash

printf "enter entrypoint.sh"
set -e

printf "\nOpenslides Database:\n"
printf "Export env variables for database.\n"
source scripts/export_database_variables.sh

printf "Database is started.\n"

printf "Create schema.\n"
python cli/create_schema.py
printf "\n"

# TODO: Re-add this code
# printf "\nMigrations:\n"
# python openslides_backend/migrations/migrate.py finalize
# printf "\n"

exec "$@"
