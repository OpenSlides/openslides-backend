#!/bin/bash

set -e

file=${1:-export.sql}
/datastore-service/cli/import-events.sh $file
