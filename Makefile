SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

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
