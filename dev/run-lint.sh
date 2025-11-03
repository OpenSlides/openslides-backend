#!/bin/bash

# Executes all linters. Should errors occur, CATCH will be set to 1, causing an erroneous exit code.

echo "########################################################################"
echo "###################### Run Linters #####################################"
echo "########################################################################"

# Parameters
while getopts "l" FLAG; do
    case "${FLAG}" in
    l) LOCAL=true ;;
    *) echo "Can't parse flag ${FLAG}" && break ;;
    esac
done

# Setup
IMAGE_TAG=openslides-backend-tests

# Helpers
DC="CONTEXT=dev docker compose -f dev/docker-compose.dev.yml"
PATHS="openslides_backend/ tests/ cli/ meta/dev/src/"

# Safe Exit
trap 'if [ -z "$LOCAL" ]; then eval "$DC down --volumes"; fi' EXIT

# Execution
if [ -z "$LOCAL" ]
then
    # Setup
    make build-tests
    eval "$DC up --build --detach"

    # Container Mode
    eval "$DC exec -T backend pyupgrade --py310-plus --exit-zero-even-if-changed $(find . -name '*.py')"
    eval "$DC exec -T backend flake8 $PATHS"
    eval "$DC exec -T backend mypy $PATHS"
    eval "$DC exec -T backend black --check $PATHS"
    eval "$DC exec -T backend autoflake --check $PATHS"
    eval "$DC exec -T backend isort --check-only $PATHS"
else
    # Local Mode
    pyupgrade --py310-plus --exit-zero-even-if-changed $(find . -name '*.py')
    eval "flake8 $PATHS"
    eval "mypy $PATHS"
    eval "black $PATHS"
    eval "autoflake $PATHS"
    eval "isort $PATHS"
fi
