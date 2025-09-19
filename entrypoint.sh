#!/bin/bash

if [ ! $ANONYMOUS_ONLY ]; then
  meta/dev/scripts/wait-for-database.sh
fi

exec "$@"
