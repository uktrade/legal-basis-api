# legal_basis_api

[![Maintainability](https://api.codeclimate.com/v1/badges/39311945e75aa22cc954/maintainability)](https://codeclimate.com/github/uktrade/legal-basis-api/maintainability) [![Test Coverage](https://api.codeclimate.com/v1/badges/39311945e75aa22cc954/test_coverage)](https://codeclimate.com/github/uktrade/legal-basis-api/test_coverage) [![Docker Repository on Quay](https://quay.io/repository/uktrade/legal-basis-api/status "Docker Repository on Quay")](https://quay.io/repository/uktrade/legal-basis-api)

Legal Basis for Consent API

This project was generated with [`wemake-django-template`](https://github.com/wemake-services/wemake-django-template). Current template version is: [66aa67fd298054b5237baad7b534e528dc153365](https://github.com/wemake-services/wemake-django-template/tree/66aa67fd298054b5237baad7b534e528dc153365). See what is [updated](https://github.com/wemake-services/wemake-django-template/compare/66aa67fd298054b5237baad7b534e528dc153365...master) since then.

## Prerequisites

You will need:

- `python3.7` (see `pyproject.toml` for full version)
- `postgresql` with version `11.6`
- `docker` (optional) with [version at least](https://docs.docker.com/compose/compose-file/#compose-and-docker-compatibility-matrix) `18.02`

## Development

When developing locally, we use:

- [`editorconfig`](http://editorconfig.org/) plugin (**required**)
- [`poetry`](https://github.com/sdispater/poetry) (**required**)

## Documentation

Full documentation is available here: [`docs/`](docs).

### Example code to register the granting or revoking of marketing consent

The API is Hawk-authenticated. From Python, the [mohawk library](https://mohawk.readthedocs.io/en/latest/) can be used to sign requests:

```python
import mohawk
import requests
import json

def hawk_request(method, url, data):
    header = mohawk.Sender({
        'id': 'REPLACE_ME',
        'key': 'REPLACE_ME',
        'algorithm': 'sha256'
    }, url, method, content_type='application/json', content=data).request_header

    requests.request(method, url, data=data, headers={
        'Authorization': header,
        'Content-Type': 'application/json',
    }).raise_for_status()

# To grant email marketing consent
hawk_request(
    method='POST',
    url="https://legal-basis-api.test/api/v1/person/",
    data=json.dumps({
        "consents": ["email_marketing"],
        "modified_at": "2021-08-27T16:37:32.229Z",
        "email": "user@domain.test",
        "key_type": "email",
    }),
)

# To grant phone marketing consent
hawk_request(
    method='POST',
    url="https://legal-basis-api.test/api/v1/person/",
    data=json.dumps({
        "consents": ["phone_marketing"],
        "modified_at": "2021-08-27T16:37:32.229Z",
        "phone": "12340000000",
        "key_type": "phone",
    }),
)

# To revoke consent
# Note the modified_at is later than the modified_at of the corresponding grant.
# The legal-basis-api assumes the most recent according to this datetime is
# current, even if they arrived at the legal-basis-api out-of-order
hawk_request(
    method='POST',
    url="https://legal-basis-api.test/api/v1/person/",
    data=json.dumps({
        "consents": [],
        "modified_at": "2021-08-27T17:12:37.123Z",
        "phone": "12340000000",
        "key_type": "phone",
    }),
)
```
