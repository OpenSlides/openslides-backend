#!/bin/bash

# Executes all linters. Should errors occur, CATCH will be set to 1, causing an erroneous exit code.

echo "########################################################################"
echo "###################### Run Linters #####################################"
echo "########################################################################"

# Parameters
while getopts "lscp" FLAG; do
    case "${FLAG}" in
    l) LOCAL=true ;;
    s) SKIP_BUILD=true ;;
    c) SKIP_CONTAINER_UP=true ;;
    p) PERSIST_CONTAINERS=true ;;
    *) echo "Can't parse flag ${FLAG}" && break ;;
    esac
done

# Setup
IMAGE_TAG=openslides-backend-tests
CATCH=0

# Helpers
USER_ID=$(id -u)
GROUP_ID=$(id -g)
DC="CONTEXT=tests USER_ID=$USER_ID GROUP_ID=$GROUP_ID docker compose -f dev/docker-compose.dev.yml"
PATHS="openslides_backend/ tests/ cli/ meta/dev/src/"

# Optionally build & start
if [ -z "$SKIP_BUILD" ]; then make build-tests || CATCH=1; fi
if [ -z "$SKIP_CONTAINER_UP" ]; then eval "$DC up --build --detach" || CATCH=1; fi

# Execution

# No difference between local and container mode
pyupgrade --py310-plus --exit-zero-even-if-changed $$(find . -name '*.py') || CATCH=1
flake8 "$PATHS" || CATCH=1
mypy "$PATHS" || CATCH=1

if [ -z "$LOCAL" ]
then
    # Container Mode
    black --check "$PATHS" || CATCH=1
    autoflake --check "$PATHS" || CATCH=1
    isort --check-only "$PATHS" || CATCH=1
else
    # Local Mode
    black "$PATHS" || CATCH=1
    autoflake "$PATHS" || CATCH=1
    isort "$PATHS" || CATCH=1
fi

if [ -z "$PERSIST_CONTAINERS" ] && [ -z "$SKIP_CONTAINER_UP" ]; then eval "$DC down --volumes" || CATCH=1; fi

exit $CATCH