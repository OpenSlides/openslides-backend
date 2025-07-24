#!/bin/bash

set -e

# Executes all tests. Should errors occur, CATCH will be set to 1, causing an erroneous exit code.

echo "########################################################################"
echo "###################### Run Tests and Linters ###########################"
echo "########################################################################"

# Parameters
while getopts "s" FLAG; do
    case "${FLAG}" in
    s) SKIP_BUILD=true ;;
    *) echo "Can't parse flag ${FLAG}" && break ;;
    esac
done

# Setup
IMAGE_TAG=openslides-backend-tests
LOCAL_PWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
export COMPOSE_DOCKER_CLI_BUILD=0

# Helpers
USER_ID=$(id -u)
GROUP_ID=$(id -g)
DC="CONTEXT=dev USER_ID=$USER_ID GROUP_ID=$GROUP_ID docker compose -f dev/docker-compose.dev.yml"

# Safe Exit
trap 'eval "$DC down --volumes"' EXIT

# Execution
if [ -z "$SKIP_BUILD" ]; then make build-tests; fi
eval "$DC up --build --detach"
eval "$DC exec -T backend scripts/wait.sh datastore-writer 9011"
eval "$DC exec -T backend scripts/wait.sh datastore-reader 9010"
eval "$DC exec -T backend scripts/wait.sh auth 9004"
eval "$DC exec -T backend ./entrypoint.sh pytest --cov"

# Linters
bash "$LOCAL_PWD"/run-lint.sh
