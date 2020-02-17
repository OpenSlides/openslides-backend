#!/bin/bash
# TODO: read optional ports from env variables: DB_PORT
wait-for-it --timeout=10 "$DB_HOST":5432

# Create schema in postgresql
export PGPASSWORD="$DB_PASSWORD"
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f src/schema.sql

exec $*

