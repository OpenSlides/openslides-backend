#!/bin/bash

meta/dev/scripts/wait-for-database.sh

exec "$@"
