# Development and testing

all:
	$(MAKE) run-cleanup
	$(MAKE) run-tests-fast

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

dev_args=--interactive --tty \
	--volume=$(dir $(mkfile_path))openslides_backend:/srv/code/openslides_backend \
	--volume=$(dir $(mkfile_path))tests:/srv/code/tests \
	--network=host --rm openslides-backend-dev

run-dev: | build-dev
	docker run $(dev_args)

run-dev-interactive run-bash: | build-dev
	docker run $(dev_args) sh

run-cleanup: | build-dev
	docker run $(dev_args) sh cleanup.sh

black: | build-dev
	docker run $(dev_args) black openslides_backend/ tests/

isort: | build-dev
	docker run $(dev_args) isort --recursive openslides_backend/ tests/

flake8: | build-dev
	docker run $(dev_args) flake8 openslides_backend/ tests/

mypy: | build-dev
	docker run $(dev_args) mypy openslides_backend/ tests/

test: | build-dev
	docker run $(dev_args) pytest

run-tests: | build-dev
	docker run $(dev_args) sh -c "OPENSLIDES_BACKEND_RUN_ALL_TESTS=1 pytest"

run-tests-fast: | build-dev
	docker run $(dev_args) pytest


run-dev-compose:
	docker-compose -f docker-compose-dev.yml up -d

stop-dev-compose:
	docker-compose down --volumes
