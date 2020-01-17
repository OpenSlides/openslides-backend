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

test_all:
	OPENSLIDES_BACKEND_RUN_ALL_TESTS=1 pytest

docker-build-dev:
	docker build -f Dockerfile-dev . -t os4-backend

docker-run-dev:
	docker run -it -v ${PWD}/openslides_backend:/srv/code/openslides_backend -p 8000:8000 --rm os4-backend
