#!/bin/bash

make build-dev

SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

BASEPATH=$SCRIPTPATH/../

docker run --interactive --tty \
    --volume=$BASEPATH/openslides_backend:/srv/code/openslides_backend \
    --volume=$BASEPATH/tests:/srv/code/tests --rm openslides-backend-dev make
