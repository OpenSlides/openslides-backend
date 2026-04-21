#!/bin/sh

export COMPOSE_DOCKER_CLI_BUILD=0

DC="CONTEXT=dev docker compose -f dev/docker-compose.dev.yml -f dev/dc.local.yml"

eval "$DC up --build --detach"
# do not execute tests as this would take too long
error=$?
eval "$DC down --volumes"
exit $error
