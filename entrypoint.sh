#!/bin/bash

source scripts/export_database_variables.sh

if [ ! $ANONYMOUS_ONLY ]; then
  meta/dev/scripts/wait-for-database.sh
fi

exec "$@"
