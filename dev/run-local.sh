#!/bin/sh

export COMPOSE_DOCKER_CLI_BUILD=0

DC="docker compose -f dev/docker-compose.dev.yml -f dev/dc.local.yml"

$DC up --build --detach
# do not execute tests as this would take too long
error=$?
$DC down --volumes
exit $error
