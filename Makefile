build-dev:
	docker build . -f Dockerfile.dev --tag openslides-media-dev

build-tests:
	docker build . -f Dockerfile.tests --tag openslides-media-tests

build-dummy-presenter:
	docker build . -f tests/dummy_presenter/Dockerfile.dummy_presenter --tag openslides-media-dummy-presenter

start-test-setup: | build-dev build-tests build-dummy-presenter
	docker-compose -f docker-compose.test.yml up -d
	docker-compose -f docker-compose.test.yml exec -T tests wait-for-it "media:9006"

run-tests: | start-test-setup
	docker-compose -f docker-compose.test.yml exec -T tests pytest

run-tests-interactive: | start-test-setup
	docker-compose -f docker-compose.test.yml exec tests bash

check-black:
	docker-compose -f docker-compose.test.yml exec -T tests black --check --diff src/ tests/

check-isort:
	docker-compose -f docker-compose.test.yml exec -T tests isort --check-only --diff src/ tests/

flake8:
	docker-compose -f docker-compose.test.yml exec -T tests flake8 src/ tests/

stop-tests:
	docker-compose -f docker-compose.test.yml down

run-cleanup: | build-dev
	docker run -ti --entrypoint="" -v `pwd`/src:/app/src -v `pwd`/tests:/app/tests openslides-media-dev bash -c "./execute-cleanup.sh"
