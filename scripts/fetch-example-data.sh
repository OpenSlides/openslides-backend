#!/bin/bash

set -e

file=${1:-example-data.json}
curl https://raw.githubusercontent.com/OpenSlides/openslides-backend/main/data/example-data.json --output $file
