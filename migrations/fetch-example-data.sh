#!/bin/bash

set -e

file=${1:-example-data.json}
curl https://raw.githubusercontent.com/OpenSlides/OpenSlides/master/docs/example-data.json --output $file
