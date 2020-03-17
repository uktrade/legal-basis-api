#!/usr/bin/env sh
set -o errexit
set -o nounset

export DJANGO_ENV

# Run python specific scripts:
# Running migrations in startup script might not be the best option, see:
# docs/pages/template/production-checklist.rst
waitress-serve --listen=0.0.0.0:$PORT --threads=${WEB_CONCURRENCY:-4} server.wsgi:application
