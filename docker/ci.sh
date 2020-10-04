#!/usr/bin/env sh

set -o errexit
set -o nounset

# Initializing global variables and functions:
: "${DJANGO_ENV:=local}"

# Fail CI if `DJANGO_ENV` is not set to `local`:
if [ "$DJANGO_ENV" != 'local' ]; then
  echo 'DJANGO_ENV is not set to local. Running tests is not safe.'
  exit 1
fi

# Python path is required for `mypy` to be run correcty with `django-stubs`:
: "${PYTHONPATH:=''}"

pyclean () {
  # Cleaning cache:
  find . | grep -E '(__pycache__|\.static|\.py[cod]$)' | xargs rm -rf
}

run_ci () {
  echo '[ci started]'

  # Running linting for all python files in the project:
  flake8 .

  # Running type checking, see https://github.com/typeddjango/django-stubs
  mypy server tests/**/*.py

  # Running tests:
  pytest --dead-fixtures --dup-fixtures
  pytest

  # Run checks to be sure settings are correct (production flag is required):
  DJANGO_ENV=production python manage.py check --deploy --fail-level WARNING

  # Check that staticfiles app is working fine:
  DJANGO_ENV=production DJANGO_COLLECTSTATIC_DRYRUN=1 \
    python manage.py collectstatic --no-input --dry-run

  # Check that all migrations worked fine:
  python manage.py makemigrations --dry-run --check

  # Check that all migrations are backwards compatible:
  python manage.py lintmigrations --exclude-apps axes sites

  # Running code-quality check:
  xenon --max-absolute A --max-modules A --max-average A server -e **/adobe.py

  # Checking if all the dependencies are secure and do not have any
  # known vulnerabilities:
  safety check --bare --full-report

  # Bandit security linting
  bandit -r .

  # Checking `pyproject.toml` file contents:
  poetry check

  # Checking dependencies status:
  pip check

  # Checking docs:
  doc8 -q docs

  # Checking `yaml` files:
  yamllint -s .

  echo '[ci finished]'
}

# Remove any cache before the script:
pyclean

# Clean everything up:
trap pyclean EXIT INT TERM

# Run the CI process:
run_ci
