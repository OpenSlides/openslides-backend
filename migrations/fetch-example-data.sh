#!/bin/bash

set -e

file=${1:-example-data.json}
curl https://raw.githubusercontent.com/OpenSlides/OpenSlides/openslides4-dev/docs/example-data.json --output $file
