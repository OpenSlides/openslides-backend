#!/bin/bash

set -e

# There is high variance between different build targets for apt-get and pip.
# Writing these installs in Dockerfile is clunky and unreadable (e.g. inline switch cases)
# Moving these installs to this install-script causes significant reduction in clutter and
# a more understandable program process

CONTEXT=${1-"prod"}
REQUIREMENTS_FILE_OVERWRITE=${2-""}

# Derive variables from build target
if [ "$CONTEXT" = "dev" ]
then
    CONTEXT_INSTALLS="make vim bash-completion"
    REQUIREMENTS_FILE="requirements_development.txt"
elif [ "$CONTEXT" = "tests" ]
then
    CONTEXT_INSTALLS="make vim bash-completion"
    REQUIREMENTS_FILE="requirements_development.txt"
else
    # Default is production target
    CONTEXT_INSTALLS="libc-dev"
    IGNORE_INSTALL_RECOMMENDS="--no-install-recommends"
    REQUIREMENTS_FILE="requirements_production.txt"
fi

if [ "$REQUIREMENTS_FILE_OVERWRITE" != "" ]
then
    REQUIREMENTS_FILE="$REQUIREMENTS_FILE_OVERWRITE"
fi

# Apt-get
apt-get -y update
apt-get -y upgrade
# shellcheck disable=SC2086
apt-get install ${IGNORE_INSTALL_RECOMMENDS} -y \
    curl \
    git \
    gcc \
    libpq-dev \
    libmagic1 \
    mime-support \
    ncat \
    ${CONTEXT_INSTALLS}

rm -rf /var/lib/apt/lists/*

# Requirements
# shellcheck disable=SC1091
. requirements/export_service_commits.sh
pip install --no-cache-dir --requirement requirements/"${REQUIREMENTS_FILE}"
