# Development and testing inside docker container or without docker (only unit and integration tests)

all: black isort flake8 mypy

black:
	black openslides_backend/ tests/

isort:
	isort openslides_backend/ tests/

flake8:
	flake8 openslides_backend/ tests/

mypy:
	mypy openslides_backend/ tests/

test:
	pytest

test-incomplete:
	pytest tests/unit tests/integration

run-debug:
	OPENSLIDES_BACKEND_DEBUG=1 python -m openslides_backend

pip-check:
	pip-check


# Build and run production docker container

build-prod:
	docker build . --tag=openslides-backend

run-prod: | build-prod
	docker run --interactive --tty \
	--publish 9002:9002 --publish 9003:9003 --rm openslides-backend


# Build and run development docker container setup with docker compose

start-dev:
	docker-compose -f dev/docker-compose.dev.yml up --build --detach

stop-dev:
	docker-compose -f dev/docker-compose.dev.yml down --volumes

start-dev-interactive:
	docker-compose -f dev/docker-compose.dev.yml up  --build

run-dev run-bash:
	docker-compose -f dev/docker-compose.dev.yml exec backend sh

run-tests:
	dev/run-tests.sh
