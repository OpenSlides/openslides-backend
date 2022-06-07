# Development and testing inside docker container or without docker (only unit and integration tests)

paths = openslides_backend/ tests/ cli/ migrations/

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

check-all: validate-models-yml check-models check-initial-data-json check-example-data-json check-permissions

validate-models-yml:
	PYTHONPATH=. python cli/modelsvalidator/validate.py

generate-models:
	PYTHONPATH=. python cli/generate_models.py $(MODELS_PATH)
	black openslides_backend/models/models.py

check-models:
	PYTHONPATH=. python cli/generate_models.py check

generate-permissions:
	PYTHONPATH=. python cli/generate_permissions.py $(MODELS_PATH)
	black openslides_backend/permissions/permissions.py

check-permissions:
	PYTHONPATH=. python cli/generate_permissions.py check

check-initial-data-json:
	PYTHONPATH=. python cli/check_json.py global/data/initial-data.json

check-example-data-json:
	PYTHONPATH=. python cli/check_json.py global/data/example-data.json

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

start-dev-attach start-dev-interactive:
	USER_ID=$$(id -u $${USER}) GROUP_ID=$$(id -g $${USER}) docker-compose -f dev/docker-compose.dev.yml up --build

stop-dev:
	docker-compose -f dev/docker-compose.dev.yml down --volumes

run-dev-attach:
	docker-compose -f dev/docker-compose.dev.yml exec backend ./entrypoint.sh bash --rcfile .bashrc

run-dev run-bash: | start-dev run-dev-attach

run-tests:
	dev/run-tests.sh


# Build and run development container with local datastore in use

start-dev-local-ds:
	USER_ID=$$(id -u $${USER}) GROUP_ID=$$(id -g $${USER}) docker-compose -f dev/docker-compose.dev.yml -f dev/dc.local-ds.yml up --build --detach

start-dev-attach-local-ds start-dev-interactive-local-ds:
	USER_ID=$$(id -u $${USER}) GROUP_ID=$$(id -g $${USER}) docker-compose -f dev/docker-compose.dev.yml -f dev/dc.local-ds.yml up --build

stop-dev-local-ds:
	docker-compose -f dev/docker-compose.dev.yml -f dev/dc.local-ds.yml down --volumes

run-dev-attach-local-ds:
	docker-compose -f dev/docker-compose.dev.yml -f dev/dc.local-ds.yml exec backend ./entrypoint.sh bash --rcfile .bashrc

run-dev-local-ds run-bash-local-ds: | start-dev-local-ds run-dev-attach-local-ds


# Build standalone development container (not usable inside the docker container)

build-dev:
	docker build --file=dev/Dockerfile.dev . --tag=openslides-backend-dev

rebuild-dev:
	docker build --file=dev/Dockerfile.dev . --tag=openslides-backend-dev --no-cache
