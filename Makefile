override SERVICE=backend
override MAKEFILE_PATH=../dev/scripts/makefile
override DOCKER_COMPOSE_FILE=./dev/docker-compose.dev.yml
override paths = openslides_backend/ tests/ cli/ meta/dev/src/

# Build images for different contexts

build build-prod build-dev build-tests:
	bash $(MAKEFILE_PATH)/make-build-service.sh $@ $(SERVICE)

# Development

.PHONY: run-dev%

run-dev%:
	bash $(MAKEFILE_PATH)/make-run-dev.sh -v "$@" "$(SERVICE)" "$(DOCKER_COMPOSE_FILE)" "$(ARGS)" "./entrypoint.sh bash --rcfile .bashrc"

# Tests

run-tests:
	bash dev/run-tests.sh

run-lint:
	bash dev/run-lint.sh -l

coverage:
	pytest --cov --cov-report html

test:
	pytest

check-all: validate-models-yml check-models check-initial-data-json check-example-data-json check-permissions

# Models

generate-models:
	python cli/generate_models.py $(MODELS_PATH)
	black openslides_backend/models/models.py

check-models:
	python cli/generate_models.py --check

validate-models-yml:
	make -C meta/dev validate-models

# Permissions

generate-permissions:
	python cli/generate_permissions.py $(MODELS_PATH)
	black openslides_backend/permissions/permissions.py

check-permissions:
	python cli/generate_permissions.py --check

check-initial-data-json:
	python cli/check_json.py data/initial-data.json

check-example-data-json:
	python cli/check_json.py data/example-data.json



########################## Deprecation List ##########################

deprecation-warning:
	bash $(MAKEFILE_PATH)/make-deprecation-warning.sh

all:
	bash $(MAKEFILE_PATH)/make-deprecation-warning.sh "run-lint"
	make run-lint

run-bash:
	bash $(MAKEFILE_PATH)/make-deprecation-warning.sh "run-dev"
	run-dev

run-dev-attach:
	bash $(MAKEFILE_PATH)/make-deprecation-warning.sh "run-dev-attached"
	run-dev-attached

stop-dev:
	bash $(MAKEFILE_PATH)/make-deprecation-warning.sh "run-dev-stop"
	CONTEXT="dev" docker compose -f dev/docker-compose.dev.yml down --volumes

check-black: | deprecation-warning
	black --check --diff $(paths)

check-pyupgrade: | deprecation-warning
	pyupgrade --py310-plus $$(find . -name '*.py')

test-unit-integration: | deprecation-warning
	pytest tests/unit tests/integration

run-debug: | deprecation-warning
	OPENSLIDES_DEVELOPMENT=1 python -m openslides_backend

pip-check: | deprecation-warning
	pip-check -H


extract-translations: | deprecation-warning
	pybabel extract --no-location --sort-output --omit-header -o openslides_backend/i18n/messages/template-en.pot openslides_backend


# Build and run production docker container (not usable inside the docker container)

run-prod: | deprecation-warning build-prod
	docker run --interactive --tty \
	--publish 9002:9002 --publish 9003:9003 --rm openslides-backend


# Build and run development docker container setup with docker compose (not usable inside docker container)

start-dev: | deprecation-warning
	CONTEXT="dev" USER_ID=$$(id -u $${USER}) GROUP_ID=$$(id -g $${USER}) docker compose -f dev/docker-compose.dev.yml up --build --detach

start-dev-attach start-dev-interactive: | deprecation-warning
	CONTEXT="dev" USER_ID=$$(id -u $${USER}) GROUP_ID=$$(id -g $${USER}) docker compose -f dev/docker-compose.dev.yml up --build

# Build and run development container with local datastore in use

start-dev-local: | deprecation-warning
	CONTEXT="dev" USER_ID=$$(id -u $${USER}) GROUP_ID=$$(id -g $${USER}) docker compose -f dev/docker-compose.dev.yml -f dev/dc.local.yml up --build --detach

start-dev-attach-local start-dev-interactive-local: | deprecation-warning
	CONTEXT="dev" USER_ID=$$(id -u $${USER}) GROUP_ID=$$(id -g $${USER}) docker compose -f dev/docker-compose.dev.yml -f dev/dc.local.yml up --build

stop-dev-local: | deprecation-warning
	CONTEXT="dev" docker compose -f dev/docker-compose.dev.yml -f dev/dc.local.yml down --volumes

run-dev-attach-local: | deprecation-warning
	CONTEXT="dev" docker compose -f dev/docker-compose.dev.yml -f dev/dc.local.yml exec backend ./entrypoint.sh bash --rcfile .bashrc

run-dev-local run-bash-local: | deprecation-warning start-dev-local run-dev-attach-local


# Build and run development container. Additionally run OpenTelemetry services

start-dev-otel: | deprecation-warning
	CONTEXT="dev" USER_ID=$$(id -u $${USER}) GROUP_ID=$$(id -g $${USER}) docker compose -f dev/docker-compose.dev.yml -f dev/dc.otel.yml up --build --detach

start-dev-attach-otel start-dev-interactive-otel: | deprecation-warning
	CONTEXT="dev" USER_ID=$$(id -u $${USER}) GROUP_ID=$$(id -g $${USER}) docker compose -f dev/docker-compose.dev.yml -f dev/dc.otel.yml up --build

stop-dev-otel: | deprecation-warning
	CONTEXT="dev" docker compose -f dev/docker-compose.dev.yml -f dev/dc.otel.yml down --volumes

run-dev-attach-otel: | deprecation-warning
	CONTEXT="dev" docker compose -f dev/docker-compose.dev.yml -f dev/dc.otel.yml exec backend ./entrypoint.sh bash --rcfile .bashrc

run-dev-otel run-bash-otel: | deprecation-warning start-dev-otel run-dev-attach-otel

rebuild-dev: | deprecation-warning
	docker build . --tag=openslides-backend-dev --no-cache --build-arg CONTEXT=dev
