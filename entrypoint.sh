#!/bin/bash

source scripts/export_datastore_variables.sh

if [ ! $ANONYMOUS_ONLY ]; then
  scripts/wait.sh $DATASTORE_WRITER_HOST $DATASTORE_WRITER_PORT
fi

echo "Test: This actually worked"

exec "$@"
