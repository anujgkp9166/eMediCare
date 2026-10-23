#!/usr/bin/env bash
# Build step for hosting services: install, collect static files, migrate, load starting data.
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py makemigrations --noinput accounts care diagnostics core
python manage.py migrate --noinput
python manage.py seed_data
