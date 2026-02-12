override SERVICE=backend
override paths = openslides_backend/ tests/ cli/ meta/dev/src/

# Build images for different contexts

build-prod:
	docker build ./ $(ARGS) --tag "openslides-$(SERVICE)" --build-arg CONTEXT="prod" --target "prod"

build-dev:
	docker build ./ $(ARGS) --tag "openslides-$(SERVICE)-dev" --build-arg CONTEXT="dev" --target "dev"

build-tests:
	docker build ./ $(ARGS) --tag "openslides-$(SERVICE)-tests" --build-arg CONTEXT="tests" --target "tests"

# Development redirects

.PHONY: dev

dev dev-help dev-standalone dev-detached dev-attached dev-stop dev-exec dev-enter dev-clean dev-build dev-log:
	@@$(MAKE) -C .. $@ backend

# Tests

run-tests:
	bash dev/run-tests.sh

lint:
	bash dev/run-lint.sh -l

test:
	pytest

coverage:
	pytest --cov --cov-report html

test-file:
# f= to pass the file name
# k= to pass a test name
# v=1 to run verbose test output
# cap=1 to capture print to system out
# cov=1 to run coverage report
	python -m debugpy --listen 0.0.0.0:5678 --wait-for-client /usr/local/bin/pytest $f $(if $(k),-k $k) $(if $(v),-vv) $(if $(cap),--capture=no) $(if $(cov),--cov --cov-report term-missing:skip-covered)

check-all: validate-models-yml check-models check-initial-data-json check-example-data-json check-permissions

# Models

generate-models:
	python cli/generate_models.py $(MODELS_PATH)
	black openslides_backend/models/models.py

check-models:
	python cli/generate_models.py --check

validate-models-yml:
	make -C meta validate-models

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
	@echo "\033[1;33m DEPRECATION WARNING: This make command is deprecated and will be removed soon! \033[0m"

deprecation-warning-alternative: | deprecation-warning
	@echo "\033[1;33m Please use the following command instead: $(ALTERNATIVE) \033[0m"

stop-dev:
	@make deprecation-warning-alternative ALTERNATIVE="dev and derivative maketargets are now only available in main repository. (use 'make dev-help' in main repository for more information)"

all: | pyupgrade black autoflake isort flake8 mypy
	@make deprecation-warning-alternative ALTERNATIVE="run-lint"

pyupgrade:
	@make deprecation-warning-alternative ALTERNATIVE="run-lint"
	pyupgrade --py310-plus --exit-zero-even-if-changed $$(find . -name '*.py')

check-pyupgrade:
	@make deprecation-warning-alternative ALTERNATIVE="run-lint"
	pyupgrade --py310-plus $$(find . -name '*.py')

black:
	@make deprecation-warning-alternative ALTERNATIVE="run-lint"
	black $(paths)

check-black:
	@make deprecation-warning-alternative ALTERNATIVE="run-lint"
	black --check --diff $(paths)

autoflake:
	@make deprecation-warning-alternative ALTERNATIVE="run-lint"
	autoflake $(paths)

isort:
	@make deprecation-warning-alternative ALTERNATIVE="run-lint"
	isort $(paths)

check-isort:
	@make deprecation-warning-alternative ALTERNATIVE="run-lint"
	isort --check-only --diff $(paths)

flake8:
	@make deprecation-warning-alternative ALTERNATIVE="run-lint"
	flake8 $(paths)

mypy:
	@make deprecation-warning-alternative ALTERNATIVE="run-lint"
	mypy $(paths)

run-bash:
	@make deprecation-warning-alternative ALTERNATIVE="dev"
	make start-dev
	make run-dev-attach

run-dev-attach:
	@make deprecation-warning-alternative ALTERNATIVE="dev-attached"
	CONTEXT="dev" USER_ID=$$(id -u $${USER}) GROUP_ID=$$(id -g $${USER}) docker compose -f dev/docker-compose.dev.yml exec backend ./entrypoint.sh bash --rcfile .bashrc

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

run-dev-local run-bash-local: | deprecation-warning start-dev-local dev-attach-local


# Build and run development container. Additionally run OpenTelemetry services

start-dev-otel: | deprecation-warning
	CONTEXT="dev" USER_ID=$$(id -u $${USER}) GROUP_ID=$$(id -g $${USER}) docker compose -f dev/docker-compose.dev.yml -f dev/dc.otel.yml up --build --detach

start-dev-attach-otel start-dev-interactive-otel: | deprecation-warning
	CONTEXT="dev" USER_ID=$$(id -u $${USER}) GROUP_ID=$$(id -g $${USER}) docker compose -f dev/docker-compose.dev.yml -f dev/dc.otel.yml up --build

stop-dev-otel: | deprecation-warning
	CONTEXT="dev" docker compose -f dev/docker-compose.dev.yml -f dev/dc.otel.yml down --volumes

run-dev-attach-otel: | deprecation-warning
	CONTEXT="dev" docker compose -f dev/docker-compose.dev.yml -f dev/dc.otel.yml exec backend ./entrypoint.sh bash --rcfile .bashrc

run-dev-otel run-bash-otel: | deprecation-warning start-dev-otel dev-attach-otel

rebuild-dev: | deprecation-warning
	docker build . --tag=openslides-backend-dev --no-cache --build-arg CONTEXT=dev
