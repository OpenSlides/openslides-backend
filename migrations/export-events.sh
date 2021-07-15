#!/bin/bash

set -e

file=${1:-export.sql}
/datastore-service/cli/export-events.sh $file
