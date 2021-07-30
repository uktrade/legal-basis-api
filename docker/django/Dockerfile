# This Dockerfile uses multi-stage build to customize DEV and PROD images:
# https://docs.docker.com/develop/develop-images/multistage-build/

FROM python:3.7-alpine as development_build

LABEL maintainer="legal_basis_api@Department for International Trade"
LABEL vendor="Department for International Trade"

ARG DJANGO_ENV

ENV DJANGO_ENV=${DJANGO_ENV} \
  # python:
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  # pip:
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  # poetry:
  POETRY_VERSION=1.0.0


# System deps:
RUN apk --no-cache add \
    bash \
    build-base \
    cargo \
    curl \
    gcc \
    gettext \
    git \
    libffi-dev \
    linux-headers \
    openssl \
    musl-dev \
    postgresql-dev \
    tini \
  # Installing `poetry` package manager:
  # https://github.com/sdispater/poetry
  && pip install -U "pip<19.0" \
  && pip install "poetry==$POETRY_VERSION"

# Copy only requirements, to cache them in docker layer:
WORKDIR /pysetup
COPY ./poetry.lock ./pyproject.toml /pysetup/

# Project initialization:
RUN poetry config virtualenvs.create false \
  && poetry install $(test "$DJANGO_ENV" == production && echo "--no-dev") --no-interaction --no-ansi

# This dir will become the mountpoint of development code:
WORKDIR /code
RUN mkdir /code/staticfiles

COPY . /code
