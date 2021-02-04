# Development and testing inside docker container or without docker (only unit and integration tests)

paths = openslides_backend/ tests/ cli/

all: black autoflake isort flake8 mypy

black:
	black $(paths)

autoflake:
	autoflake --verbose --in-place --remove-all-unused-imports \
	--ignore-init-module-imports --recursive $(paths)

isort:
	isort $(paths)

flake8:
	flake8 $(paths)

mypy:
	mypy $(paths)

test:
	pytest

test-unit-integration:
	pytest tests/unit tests/integration

generate-models:
	PYTHONPATH=. python3 cli/generate_models.py
	black openslides_backend/models/models.py

check-models:
	PYTHONPATH=. python cli/generate_models.py check

run-debug:
	OPENSLIDES_DEVELOPMENT=1 python -m openslides_backend

pip-check:
	pip-check

coverage:
	pytest --cov --cov-report html


# Build and run production docker container (not usable inside the docker container)

build-prod:
	docker build . --tag=openslides-backend

run-prod: | build-prod
	docker run --interactive --tty \
	--publish 9002:9002 --publish 9003:9003 --rm openslides-backend


# Build and run development docker container setup with docker compose (not usable inside docker container)

start-dev:
	USER_ID=$$(id -u $${USER}) GROUP_ID=$$(id -g $${USER}) docker-compose -f dev/docker-compose.dev.yml up --build --detach

stop-dev:
	docker-compose -f dev/docker-compose.dev.yml down --volumes

start-dev-interactive:
	USER_ID=$$(id -u $${USER}) GROUP_ID=$$(id -g $${USER}) docker-compose -f dev/docker-compose.dev.yml up --build

run-dev-standalone: | start-dev
	docker-compose -f dev/docker-compose.dev.yml exec backend bash --rcfile dev/bashrc

run-dev run-bash: | run-dev-standalone

run-tests:
	dev/run-tests.sh


# Build standalone development container (not usable inside the docker container)

build-dev:
	docker build --file=dev/Dockerfile-dev . --tag=openslides-backend-dev
