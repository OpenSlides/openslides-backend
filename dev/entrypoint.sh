#!/bin/bash

printf "enter entrypoint.sh"
set -e

printf "\nOpenslides DBMS:\n"
printf "Export env variables for database.\n"
source scripts/export_database_variables.sh

# Wait for Database
meta/dev/scripts/wait-for-database.sh
printf "DBMS is started.\n"

printf "Calling cli/create_schema.py ...\n"
python cli/create_schema.py
printf "\n"

printf "\nMigrations:\n"
python openslides_backend/migrations/migrate.py finalize
printf "\n"

# Prune old blocked sessions
if [ "$OPENSLIDES_DEVELOPMENT" = 1 ] || [ "$OPENSLIDES_BACKEND_COMPONENT" = "manage" ]; then
  prune_loop() {
    while true; do
      # 259200 = 3 days
      sleep 259200
      python /app/cli/prune-blocked-sessions.py || true
    done
  }
  prune_loop &
fi

exec "$@"
