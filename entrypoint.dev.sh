#!/bin/bash
set -e

bash entrypoint.sh

# load test data in postgresql
PGPASSWORD="openslides" psql -1 -h "$MEDIA_DATABASE_HOST" -U "openslides" -d "$MEDIA_DATABASE_NAME" -f src/test_data.sql

exec "$@"

