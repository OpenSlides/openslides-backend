#!/bin/sh

export COMPOSE_DOCKER_CLI_BUILD=0

DC="CONTEXT=dev docker compose -f dev/docker-compose.dev.yml -f dev/dc.local.yml"

eval "$DC up --build --detach"
eval "$DC exec -T backend scripts/wait.sh datastore-writer 9011"
eval "$DC exec -T backend scripts/wait.sh datastore-reader 9010"
# do not execute tests as this would take too long
error=$?
eval "$DC down --volumes"
exit $error
