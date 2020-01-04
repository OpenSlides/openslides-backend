all: black isort flake8 mypy test

black:
	black openslides_backend/ tests/ start.py

isort:
	isort --recursive openslides_backend/ tests/ start.py

flake8:
	flake8 openslides_backend/ tests/ start.py

mypy:
	mypy openslides_backend/ tests/ start.py

test:
	pytest
