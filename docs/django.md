# Django

## Configuration

We share the same configuration structure for almost every possible
environment.

We use:

- `django-split-settings` to organize `django` settings into multiple files and directories
- `.env` files to store secret configuration
- `python-decouple` to load `.env` files into `django`

### Components

If you have some specific components like `celery` or `mailgun`
installed, they could be configured in separate files. Just create a new
file in `server/settings/components/`. Then add it into
`server/settings/__init__.py`.

### Environments

To run `django` on different environments just specify `DJANGO_ENV`
environment variable. It must have the same name as one of the files
from `server/settings/environments/`. Then, values from this file will
override other settings.
