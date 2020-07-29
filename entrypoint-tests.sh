#!/bin/bash

wait-for-it -t 0 "media:9006"

black src/ tests/ && isort --recursive src/ tests/ && flake8 src/ tests/ && \
	pytest
