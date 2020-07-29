#!/bin/bash

wait-for-it -t 0 "media:9006"

exec "$@"
