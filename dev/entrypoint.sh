#!/bin/bash

set -e

source scripts/export_database_variables.sh

printf "\nOpenslides Database:\n"
python cli/create_schema.py
printf "\n"

# TODO: Re-add this code
# printf "\nMigrations:\n"
# python openslides_backend/migrations/migrate.py finalize
# printf "\n"

exec "$@"
