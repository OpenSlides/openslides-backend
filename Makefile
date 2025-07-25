SERVICE=backend

# Build images for different contexts

build-prod:
	docker build ./ --tag "openslides-$(SERVICE)" --build-arg CONTEXT="prod" --target "prod"

build-dev:
	docker build ./ --tag "openslides-$(SERVICE)-dev" --build-arg CONTEXT="dev" --target "dev"

build-test:
	docker build ./ --tag "openslides-$(SERVICE)-tests" --build-arg CONTEXT="tests" --target "tests"


# Development and testing inside docker container or without docker (only unit and integration tests)

paths = openslides_backend/ tests/ cli/ meta/dev/src/

all: pyupgrade black autoflake isort flake8 mypy

pyupgrade:
	pyupgrade --py310-plus --exit-zero-even-if-changed $$(find . -name '*.py')

check-pyupgrade:
	pyupgrade --py310-plus $$(find . -name '*.py')

black:
	black $(paths)

check-black:
	black --check --diff $(paths)

autoflake:
	autoflake $(paths)

isort:
	isort $(paths)

check-isort:
	isort --check-only --diff $(paths)

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
	make -C meta/dev validate-models

generate-models:
	python cli/generate_models.py $(MODELS_PATH)
	black openslides_backend/models/models.py

check-models:
	python cli/generate_models.py --check

generate-permissions:
	python cli/generate_permissions.py $(MODELS_PATH)
	black openslides_backend/permissions/permissions.py

check-permissions:
	python cli/generate_permissions.py --check

check-initial-data-json:
	python cli/check_json.py data/initial-data.json

check-example-data-json:
	python cli/check_json.py data/example-data.json

run-debug:
	OPENSLIDES_DEVELOPMENT=1 python -m openslides_backend

pip-check:
	pip-check -H

coverage:
	pytest --cov --cov-report html

extract-translations:
	pybabel extract --no-location --sort-output --omit-header -o openslides_backend/i18n/messages/template-en.pot openslides_backend


# Build and run production docker container (not usable inside the docker container)

run-prod: | build-prod
	docker run --interactive --tty \
	--publish 9002:9002 --publish 9003:9003 --rm openslides-backend


# Build and run development docker container setup with docker compose (not usable inside docker container)

start-dev:
	CONTEXT="dev" USER_ID=$$(id -u $${USER}) GROUP_ID=$$(id -g $${USER}) docker compose -f dev/docker-compose.dev.yml up --build --detach

start-dev-attach start-dev-interactive:
	CONTEXT="dev" USER_ID=$$(id -u $${USER}) GROUP_ID=$$(id -g $${USER}) docker compose -f dev/docker-compose.dev.yml up --build

stop-dev:
	CONTEXT="dev" docker compose -f dev/docker-compose.dev.yml down --volumes

run-dev-attach:
	CONTEXT="dev" docker compose -f dev/docker-compose.dev.yml exec backend ./entrypoint.sh bash --rcfile .bashrc

run-dev run-bash: | start-dev run-dev-attach

run-tests:
	bash dev/run-tests.sh


# Build and run development container with local datastore in use

start-dev-local:
	CONTEXT="dev" USER_ID=$$(id -u $${USER}) GROUP_ID=$$(id -g $${USER}) docker compose -f dev/docker-compose.dev.yml -f dev/dc.local.yml up --build --detach

start-dev-attach-local start-dev-interactive-local:
	CONTEXT="dev" USER_ID=$$(id -u $${USER}) GROUP_ID=$$(id -g $${USER}) docker compose -f dev/docker-compose.dev.yml -f dev/dc.local.yml up --build

stop-dev-local:
	CONTEXT="dev" docker compose -f dev/docker-compose.dev.yml -f dev/dc.local.yml down --volumes

run-dev-attach-local:
	CONTEXT="dev" docker compose -f dev/docker-compose.dev.yml -f dev/dc.local.yml exec backend ./entrypoint.sh bash --rcfile .bashrc

run-dev-local run-bash-local: | start-dev-local run-dev-attach-local


# Build and run development container. Additionally run OpenTelemetry services

start-dev-otel:
	CONTEXT="dev" USER_ID=$$(id -u $${USER}) GROUP_ID=$$(id -g $${USER}) docker compose -f dev/docker-compose.dev.yml -f dev/dc.otel.yml up --build --detach

start-dev-attach-otel start-dev-interactive-otel:
	CONTEXT="dev" USER_ID=$$(id -u $${USER}) GROUP_ID=$$(id -g $${USER}) docker compose -f dev/docker-compose.dev.yml -f dev/dc.otel.yml up --build

stop-dev-otel:
	CONTEXT="dev" docker compose -f dev/docker-compose.dev.yml -f dev/dc.otel.yml down --volumes

run-dev-attach-otel:
	CONTEXT="dev" docker compose -f dev/docker-compose.dev.yml -f dev/dc.otel.yml exec backend ./entrypoint.sh bash --rcfile .bashrc

run-dev-otel run-bash-otel: | start-dev-otel run-dev-attach-otel

rebuild-dev:
	docker build . --tag=openslides-backend-dev --no-cache --build-arg CONTEXT=dev
