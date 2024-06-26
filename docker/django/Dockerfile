# This Dockerfile uses multi-stage build to customize DEV and PROD images:
# https://docs.docker.com/develop/develop-images/multistage-build/

FROM python:3.10-alpine as development_build

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
  # cryptography
  CRYPTOGRAPHY_DONT_BUILD_RUST=1

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
    python3-dev \
    cargo \
  && pip install --upgrade pip wheel

# Copy only requirements, to cache them in docker layer:
COPY requirements-dev.txt /

# Project initialization:
RUN python3 -m pip install -r requirements-dev.txt

# This dir will become the mountpoint of development code:
WORKDIR /code
RUN mkdir /code/staticfiles

COPY . /code
