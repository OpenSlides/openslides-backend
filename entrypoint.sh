#!/bin/bash

source scripts/export_database_variables.sh

printf "Create schema.\n"
python cli/create_schema.py
printf "\n"

if [ ! $ANONYMOUS_ONLY ]; then
  meta/dev/scripts/wait-for-database.sh
fi

exec "$@"
