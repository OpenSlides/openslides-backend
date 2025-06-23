#!/bin/sh

if [ ! -z "$dev"   ]; then exec python -m debugpy --listen 0.0.0.0:5678 openslides_backend; fi
if [ ! -z "$prod"  ]; then exec python -m openslides_backend; fi