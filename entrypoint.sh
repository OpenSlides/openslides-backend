#!/bin/bash

printf "enter entrypoint.sh"
set -e

printf "\nOpenslides DBMS:\n"
printf "Export env variables for database.\n"
source scripts/export_database_variables.sh

if [ ! $ANONYMOUS_ONLY ]; then
  meta/dev/scripts/wait-for-database.sh
  printf "DBMS is started.\n"
fi

if [ "$ACTION_HOST" = "backendManage" || "$APP_CONTEXT" = "dev" ]; then
  printf "Create schema.\n"
  python cli/create_schema.py
  printf "\n"
fi

exec "$@"
