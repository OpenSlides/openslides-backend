#!/bin/bash

source scripts/export_datastore_variables.sh
scripts/wait.sh $DATASTORE_WRITER_HOST $DATASTORE_WRITER_PORT

exec "$@"
