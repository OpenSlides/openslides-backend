#!/bin/bash

# Executes all tests. Should errors occur, CATCH will be set to 1, causing an erroneous exit code.

echo "########################################################################"
echo "###################### Run Tests and Linters ###########################"
echo "########################################################################"

# Setup
IMAGE_TAG=openslides-backend-tests
CATCH=0
export COMPOSE_DOCKER_CLI_BUILD=0

# Safe Exit
trap 'eval "$DC down --volumes' EXIT

# Helpers
USER_ID=$(id -u)
GROUP_ID=$(id -g)
DC="CONTEXT=tests USER_ID=$USER_ID GROUP_ID=$GROUP_ID docker compose -f dev/docker-compose.dev.yml"

# Execution
if [ "$(docker images -q $IMAGE_TAG)" = "" ]; then make build-test || CATCH=1; fi
eval "$DC up --build --detach || CATCH=1"
eval "$DC exec -T backend scripts/wait.sh datastore-writer 9011 || CATCH=1"
eval "$DC exec -T backend scripts/wait.sh datastore-reader 9010 || CATCH=1"
eval "$DC exec -T backend scripts/wait.sh auth 9004 || CATCH=1"
eval "$DC exec -T backend ./entrypoint.sh pytest --cov  || CATCH=1"

exit $CATCH
