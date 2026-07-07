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

  # Wait for Keycloak
  #until curl -f "$KEYCLOAK_URL_INTERNAL/realms/openslides/.well-known/openid-configuration" > /dev/null 2>&1; do
  #  printf "Waiting for keycloak\n"
  #  sleep 3
  #done
fi

printf "Creating schema ...\n"
python cli/create_schema.py
printf "\n"

exec "$@"
