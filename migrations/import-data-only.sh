#!/bin/bash

set -e

file=${1:-export.json}
python /datastore-service/cli/import_data_only.py < $file
