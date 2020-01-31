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
