#!/bin/bash

printf "enter entrypoint.sh"
set -e

printf "\nOpenslides DBMS:\n"
printf "Export env variables for database.\n"
source scripts/export_database_variables.sh

if [ ! $ANONYMOUS_ONLY ]; then
  # Wait for Database
  meta/dev/scripts/wait-for-database.sh
  printf "DBMS is started.\n"

fi

printf "Creating schema ...\n"
python cli/create_schema.py
printf "\n"

# Export Environment, so that the pruning cron job can read database env variables
export -p > /etc/cron-env.sh
chmod 600 /etc/cron-env.sh
cron

exec "$@"
