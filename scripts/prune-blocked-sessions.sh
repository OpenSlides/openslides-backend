#!/bin/bash
set -ea pipefail

# Load Environment
source /etc/cron-env.sh

echo "HERE"

# Check if manager container or in dev mode
if [ "$OPENSLIDES_DEVELOPMENT" != 1 ] && [ "$OPENSLIDES_BACKEND_COMPONENT" != "manage" ]; then exit 0; fi

# Executing SQL Statement in Python Script, since psql is not available in prod
/usr/local/bin/python /app/cli/prunbe-blocked-sessions.py
