#!/bin/bash
set -e

source scripts/service_env.sh

until pg_isready -h "$MEDIA_DATABASE_HOST" -p "$MEDIA_DATABASE_PORT"; do
    echo "Waiting for Postgres server '$MEDIA_DATABASE_HOST' to become available..."
    sleep 3
done

PSQL="psql -1 -h "$MEDIA_DATABASE_HOST" -p "$MEDIA_DATABASE_PORT" -U "$MEDIA_DATABASE_USER" -d "$MEDIA_DATABASE_NAME""

# Create schema in postgresql
$PSQL -f src/schema.sql

# load test data in postgresql
if [[ $MEDIA_ADD_TEST_FILES -eq 1 ]]; then
    $PSQL -f src/test_data.sql
fi

exec "$@"

