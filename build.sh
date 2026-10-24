#!/usr/bin/env bash
# Render build script. Free web services have no pre-deploy hook, so migrate runs here.
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
