# Development and testing

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

run-tests:
	echo "This has to be fixed."
	OPENSLIDES_BACKEND_RUN_ALL_TESTS=1 pytest
	# TODO: Run tests inside a container.

pip-check:
	pip-check

run-debug:
	OPENSLIDES_BACKEND_DEBUG=1 python -m openslides_backend


# Build an run production container

build-prod:
	docker build --file=Dockerfile . --tag=openslides-backend

run-prod:
	docker run --interactive --tty \
	--publish 9002:9002 --publish 9003:9003 --rm openslides-backend


# Build and run development and testing containers

build-dev:
	docker build --file=Dockerfile-dev . --tag openslides-backend-dev

mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))

run-dev:
	docker run --interactive --tty --volume=$(dir $(mkfile_path))openslides_backend:/srv/code/openslides_backend \
	--publish 9002:9002 --publish 9003:9003 --rm openslides-backend-dev

run-dev-interactive:
	docker run --interactive --tty --volume=$(dir $(mkfile_path))openslides_backend:/srv/code/openslides_backend \
	--publish 9002:9002 --publish 9003:9003 --rm openslides-backend-dev sh

run-dev-compose:
	docker-compose -f docker-compose-dev.yml up -d

stop-dev-compose:
	docker-compose down --volumes
