#!/bin/sh

export COMPOSE_DOCKER_CLI_BUILD=0

DC="docker-compose -f dev/docker-compose.dev.yml"

$DC up --build --detach
$DC exec -T backend dev/wait.sh writer 9011
$DC exec -T backend dev/wait.sh reader 9010
$DC exec -T backend dev/wait.sh auth 9004
$DC exec -T backend pytest --cov
error=$?
$DC down --volumes
exit $error
