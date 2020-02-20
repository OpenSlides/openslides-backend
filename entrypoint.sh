#!/bin/bash
# TODO: read optional ports from env variables: DB_PORT
until pg_isready -h "$DB_HOST"; do
  echo "Waiting for Postgres server '$DB_HOST' to become available..."
  sleep 3
done

# Create schema in postgresql
export PGPASSWORD="$DB_PASSWORD"
psql -1 -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f src/schema.sql

exec "$@"
