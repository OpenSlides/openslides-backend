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

run-unit-tests: | build-dev
	docker run $(dev_args) pytest tests/unit/


# testing
# -T is important for GH actions: There is no TTY

DC=docker-compose -f docker-compose.dev.yml

build-tests: | build-dev
	$(DC) build

start-test-setup: | build-tests
	$(DC) up -d
	$(DC) exec -T backend ./wait.sh writer 9011
	$(DC) exec -T backend ./wait.sh reader 9010

start-test-setup-verbose: | build-tests
	$(DC) up
	$(DC) exec -T backend ./wait.sh writer 9011
	$(DC) exec -T backend ./wait.sh reader 9010

run-tests-interactive: | start-test-setup
	$(DC) exec backend sh

run-tests: | start-test-setup
	$(DC) exec backend pytest
	$(DC) down --volumes

run-tests-cov: | start-test-setup
	$(DC) exec backend pytest --cov
	$(DC) down --volumes

ci-run-tests-cov: | start-test-setup
	$(DC) exec -T backend pytest --cov
	$(DC) down --volumes

stop-tests:
	$(DC) down --volumes

# other github actions commands (no tty available)

ci-black-check: | build-dev
	docker run $(action_args) black --check --diff openslides_backend/ tests/

ci-isort-check: | build-dev
	docker run $(action_args) isort --check-only --diff openslides_backend/ tests/

ci-flake8-check: | build-dev
	docker run $(action_args) flake8 openslides_backend/ tests/

ci-mypy-check: | build-dev
	docker run $(action_args) mypy openslides_backend/ tests/
