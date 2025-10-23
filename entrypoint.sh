#!/bin/bash

source scripts/export_datastore_variables.sh

if [ ! $ANONYMOUS_ONLY ]; then
  meta/dev/scripts/wait-for-database.sh
fi

exec "$@"
