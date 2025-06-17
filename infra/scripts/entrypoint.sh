#!/bin/bash

# if any of the commands in your code fails for any reason, the entire script fails
set -o errexit
# fail exit if one of your pipe command fails
set -o pipefail
# exits if any of your variables is not set
set -o nounset

echo "Collecting static files..."
if ! python3 ./manage.py collectstatic --no-input; then
  echo "Failed to collect static files"
  exit 1
fi
echo "Static files collected successfully"

echo "Applying database migrations..."
if ! python3 ./manage.py migrate; then
  echo "Failed to apply database migrations"
  exit 1
fi

# Need for websocket
# export DJANGO_SETTINGS_MODULE=config.settings

exec "$@"
