#!/bin/bash

# Executes all tests. Should errors occur, CATCH will be set to 1, causing an erronous exit code.

echo "########################################################################"
echo "###################### Run Tests and Linters ###########################"
echo "########################################################################"

IMAGE_TAG=openslides-backend-dev
CATCH=0
PERSIST_CONTAINERS=$1
export COMPOSE_DOCKER_CLI_BUILD=0

DC="docker compose -f dev/docker-compose.dev.yml"

if [ "$(docker images -q $IMAGE_TAG)" = "" ]; then make build-dev || CATCH=1; fi
$DC up --build --detach || CATCH=1
$DC exec -T backend scripts/wait.sh datastore-writer 9011 || CATCH=1
$DC exec -T backend scripts/wait.sh datastore-reader 9010 || CATCH=1
$DC exec -T backend scripts/wait.sh auth 9004 || CATCH=1
$DC exec -T backend ./entrypoint.sh pytest --cov || CATCH=1

if [ -z $PERSIST_CONTAINERS ]; then $DC down --volumes || CATCH=1; fi

exit $CATCH
