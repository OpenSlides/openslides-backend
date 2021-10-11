#!/bin/bash
set -e

bash entrypoint.sh

# load test data in postgresql
PGPASSWORD="$MEDIA_DATABASE_PASSWORD" psql -1 -h "$MEDIA_DATABASE_HOST" -U "$MEDIA_DATABASE_USER" -d "$MEDIA_DATABASE_NAME" -f src/test_data.sql

exec "$@"

