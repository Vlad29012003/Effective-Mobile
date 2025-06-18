#!/bin/sh

set -o errexit
set -o nounset

gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --threads 8 --timeout 60 --max-requests 30000 --max-requests-jitter 10000
