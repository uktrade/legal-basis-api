#!/bin/bash -xe
python manage.py migrate
python manage.py collectstatic --noinput
python -Wd manage.py runserver 0.0.0.0:8000