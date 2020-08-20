# Development and testing without docker

all: black isort flake8 mypy test

black:
	black openslides_backend/ tests/

isort:
	isort --recursive openslides_backend/ tests/

flake8:
	flake8 openslides_backend/ tests/

mypy:
	mypy openslides_backend/ tests/

test:
	pytest

run-debug:
	OPENSLIDES_BACKEND_DEBUG=1 python -m openslides_backend

pip-check:
	pip-check


# Build and run production docker container

build-prod:
	docker build --file=Dockerfile . --tag=openslides-backend

run-prod:
	docker run --interactive --tty \
	--publish 9002:9002 --publish 9003:9003 --rm openslides-backend


# Build and run development and testing docker container

build-dev:
	docker build --file=Dockerfile-dev . --tag openslides-backend-dev

mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))

action_args=--interactive \
	--volume=$(dir $(mkfile_path))openslides_backend:/srv/code/openslides_backend \
	--volume=$(dir $(mkfile_path))tests:/srv/code/tests \
	--network=host --rm openslides-backend-dev
dev_args=--tty $(action_args)

run-dev: | build-dev
	docker run $(dev_args)

run-dev-interactive run-bash: | build-dev
	docker run $(dev_args) sh

run-cleanup: | build-dev
	docker run $(dev_args) sh cleanup.sh

run-black: | build-dev
	docker run $(dev_args) black openslides_backend/ tests/

run-isort: | build-dev
	docker run $(dev_args) isort --recursive openslides_backend/ tests/

run-flake8: | build-dev
	docker run $(dev_args) flake8 openslides_backend/ tests/

run-mypy: | build-dev
	docker run $(dev_args) mypy openslides_backend/ tests/

run-unit-tests: | build-dev
	docker run $(dev_args) pytest tests/unit/


# compose commands

COMPOSE_FILE=docker-compose.dev.yml

run-dev-compose: | build-dev
	docker-compose -f $(COMPOSE_FILE) up -d

run-dev-verbose: | build-dev
	docker-compose -f $(COMPOSE_FILE) up

stop-dev-compose:
	docker-compose -f $(COMPOSE_FILE) down --volumes

run-compose-bash: | run-dev-compose
	docker-compose -f $(COMPOSE_FILE) exec backend sh

run-tests: | run-dev-compose
	docker-compose -f $(COMPOSE_FILE) exec backend pytest
	docker-compose -f $(COMPOSE_FILE) down --volumes

run-tests-cov: | run-dev-compose
	docker-compose -f $(COMPOSE_FILE) exec backend pytest --cov
	docker-compose -f $(COMPOSE_FILE) down --volumes

run-tests-cov-no-tty: | run-dev-compose
	docker run $(action_args) pytest --cov


# other github actions commands (no tty available)

run-black-check: | build-dev
	docker run $(action_args) black --check --diff openslides_backend/ tests/

run-isort-check: | build-dev
	docker run $(action_args) isort --check-only --diff openslides_backend/ tests/

run-flake8-check: | build-dev
	docker run $(action_args) flake8 openslides_backend/ tests/

run-mypy-check: | build-dev
	docker run $(action_args) mypy openslides_backend/ tests/
