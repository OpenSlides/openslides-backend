#!/bin/bash

wait-for-it -t 0 "media:8000"

exec "$@"
