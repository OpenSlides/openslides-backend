#!/bin/bash
set -e

export MEDIA_DATABASE_HOST="${MEDIA_DATABASE_HOST:-db}"
export MEDIA_DATABASE_PORT="${MEDIA_DATABASE_PORT:-5432}"
export MEDIA_DATABASE_NAME="${MEDIA_DATABASE_NAME:-mediafiledata}"
export MEDIA_DATABASE_USER="${MEDIA_DATABASE_USER:-openslides}"
export MEDIA_DATABASE_PASSWORD="${MEDIA_DATABASE_PASSWORD:-openslides}"
PGPASSWORD="$MEDIA_DATABASE_PASSWORD"

until pg_isready -h "$MEDIA_DATABASE_HOST" -p "$MEDIA_DATABASE_PORT"; do
  echo "Waiting for Postgres server '$MEDIA_DATABASE_HOST' to become available..."
  sleep 3
done

# Create schema in postgresql
PGPASSWORD="$MEDIA_DATABASE_PASSWORD" psql -1 -h "$MEDIA_DATABASE_HOST" -U "$MEDIA_DATABASE_USER" -d "$MEDIA_DATABASE_NAME" -f src/schema.sql
PGPASSWORD="$MEDIA_DATABASE_PASSWORD" psql -1 -h "$MEDIA_DATABASE_HOST" -U "$MEDIA_DATABASE_USER" -d "$MEDIA_DATABASE_NAME" -f src/test_data.sql

exec "$@"
