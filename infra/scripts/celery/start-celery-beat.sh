#!/bin/bash

set -o errexit
set -o nounset

# Check environment variable first (highest priority)
if [ -n "${DEBUG+x}" ]; then
  DEBUG_VALUE=$DEBUG
else
  # If env var is not set, parse from .env file
  if [ -f ".env" ]; then
    DEBUG_VALUE=$(grep -E "^DEBUG=" .env | cut -d= -f2)
  else
    # Default value if neither env var nor .env exists
    DEBUG_VALUE="False"
  fi
fi

# Set loglevel based on DEBUG_VALUE
LOGLEVEL="info"
if [ "$DEBUG_VALUE" = "True" ]; then
  LOGLEVEL="debug"
fi

celery -A config beat --loglevel=${LOGLEVEL}
