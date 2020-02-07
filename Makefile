SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules
MAKEFLAGS += -j

ifeq ($(origin .RECIPEPREFIX), undefined)
  $(error This Make does not support .RECIPEPREFIX. Please use GNU Make 4.0 or later)
endif
.RECIPEPREFIX = >

# Default - top level rule is what gets ran when you run just `make`
build:
.PHONY: build

# Clean up the output directories; since all the sentinel files go under tmp, this will cause everything to get rebuilt
clean:
> rm -rf ./staticfiles
> rm -rf ./htmlcov
> rm -rf ./pytest_cache
> rm -rf ./.mypy_cache
> rm -rf ./.cache
> rm -rf ./.hypothesis
> rm -rf ./.pytest_cache
> rm ./requirements.txt
> poetry run ./manage.py clean_pyc
.PHONY: clean

requirements: poetry.lock
> poetry export --without-hashes -f requirements.txt -o requirements.txt

deploy: requirements
> cf push
.PHONY: deploy

test:
> poetry run pytest
.PHONY: test

lint-migrations:
> poetry run ./manage.py lintmigrations --exclude-apps axes sites
.PHONY: lint-migrations

flake8:
> poetry run flake8 .
.PHONY: flake8

lint-types:
> poetry run mypy server
.PHONY: lint-types

lint-dotenv:
> dotenv-linter config/.env config/.env.template
.PHONY: lint-dotenv

lint-pip:
> poetry check && poetry run pip check
.PHONY: lint-pip

lint-code-quality:
> poetry run xenon --max-absolute A --max-modules A --max-average A server
.PHONY: lint-code-quality

lint: lint-migrations flake8 lint-types lint-dotenv lint-pip lint-code-quality
> @echo "Running lint"
.PHONY: lint
