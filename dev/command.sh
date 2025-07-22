#!/bin/sh

if [ "$APP_CONTEXT" = "dev"   ]; then exec python -m debugpy --listen 0.0.0.0:5678 openslides_backend; fi
if [ "$APP_CONTEXT" = "prod"   ]; then exec python -m openslides_backend; fi