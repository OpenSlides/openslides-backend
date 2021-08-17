#!/bin/bash

printf "Black:\n"
black .
printf "\nIsort:\n"
isort .
printf "\nFlake8:\n"
flake8 .
printf "\nmypy:\n"
mypy .
