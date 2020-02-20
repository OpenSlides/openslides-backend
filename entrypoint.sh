#!/bin/bash

export DB_HOST="${DB_HOST:-db}"
export DB_PORT="${DB_PORT:-5432}"
export DB_NAME="${DB_NAME:-mediafiledata}"
export DB_USER="${DB_USER:-openslides}"
export PGPASSWORD="${DB_PASSWORD:-openslides}"

until pg_isready -h "$DB_HOST" -p "$DB_PORT"; do
  echo "Waiting for Postgres server '$DB_HOST' to become available..."
  sleep 3
done

# Create schema in postgresql
psql -1 -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f src/schema.sql

exec "$@"
