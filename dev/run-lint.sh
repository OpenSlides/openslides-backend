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
PATHS="openslides_backend/ tests/ cli/"

# Safe Exit
trap 'if [ -z "$LOCAL" ]; then eval "$DC down --volumes"; fi' EXIT

# Execution
if [ -z "$LOCAL" ]
then
    # Setup
    make build-tests
    eval "$DC up --build --detach"

    # Container Mode
    echo "Running pyupgrade"
    eval "$DC exec -T backend pyupgrade --py310-plus --exit-zero-even-if-changed $(find . -name '*.py')"
    echo "Running black"
    eval "$DC exec -T backend black --check $PATHS"
    echo "Running autoflake"
    eval "$DC exec -T backend autoflake --check $PATHS"
    echo "Running isort"
    eval "$DC exec -T backend isort --check-only $PATHS"
    echo "Running flake8"
    eval "$DC exec -T backend flake8 $PATHS"
    echo "Running mypy"
    eval "$DC exec -T backend mypy $PATHS"
    echo "Running sqruff"
    eval "$DC exec -T backend sqruff fix $PATHS --config setup.cfg"
else
    # Local Mode
    echo "Running pyupgrade"
    pyupgrade --py310-plus --exit-zero-even-if-changed $(find . -name '*.py')
    echo "Running black"
    eval "black $PATHS"
    echo "Running autoflake"
    eval "autoflake $PATHS"
    echo "Running isort"
    eval "isort $PATHS"
    echo "Running flake8"
    eval "flake8 $PATHS"
    echo "Running mypy"
    eval "mypy $PATHS"
    echo "Running sqruff"
    eval "sqruff fix $PATHS --config setup.cfg"
fi
