#!/bin/bash

printf "Black:\n"
black src/ tests/
printf "\nIsort:\n"
isort src/ tests/
printf "\nFlake8:\n"
flake8 src/ tests/