#!/bin/bash

printf "Black:\n"
black openslides_backend tests cli
printf "\nIsort:\n"
isort openslides_backend tests cli
printf "\nFlake8:\n"
flake8 openslides_backend tests cli
printf "\nmypy:\n"
mypy openslides_backend tests cli
