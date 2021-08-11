#!/bin/bash

make build-dev

SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

BASEPATH=$SCRIPTPATH/../

docker run --interactive --tty \
    --volume=$BASEPATH/openslides_backend:/app/openslides_backend \
    --volume=$BASEPATH/migrations:/app/migrations \
    --volume=$BASEPATH/tests:/app/tests \
    --volume=$BASEPATH/cli:/app/cli --rm --entrypoint="" openslides-backend-dev make
