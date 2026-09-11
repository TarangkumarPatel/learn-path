#!/bin/sh
set -e

mkdir -p /data

python manage.py migrate

PORT="${PORT:-8000}"

exec gunicorn learnpath.wsgi:application --bind "0.0.0.0:${PORT}"
