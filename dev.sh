#!/bin/bash
cd src
export FLASK_APP=mediaserver
export FLASK_ENV=development
flask run
