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

### Example code to register marketing consent

The API is Hawk-authenticated. From Python, the [mohawk library](https://mohawk.readthedocs.io/en/latest/) can be used to sign requests:

```python
import mohawk
import requests
import json

def hawk_request(method, url, key_id, secret_key, data):
    header = mohawk.Sender({
        'id': key_id,
        'key': secret_key,
        'algorithm': 'sha256'
    }, url, method, content_type='application/json', content=data).request_header

    requests.request(method, url, data=data, headers={
        'Authorization': header,
        'Content-Type': 'application/json',
    }).raise_for_status()

# To record email marketing consent
hawk_request(
    method='POST',
    url="https://legal-basis-api.test/api/v1/person/",
    key_id="REPLACE_ME",
    secret_key='REPLACE_ME',
    data=json.dumps({
	  "consents": ["email_marketing"],
	  "modified_at": "2021-08-27T16:37:32.229Z",
	  "email": "user@domain.test",
	  "key_type": "email"
	}),
)

# To record phone marketing consent
hawk_request(
    method='POST',
    url="https://legal-basis-api.test/api/v1/person/",
    key_id="REPLACE_ME",
    secret_key="REPLACE_ME",
    data=json.dumps({
        "consents": ["phone_marketing"],
        "modified_at": "2021-08-27T16:37:32.229Z",
        "phone": "12340000000",
        "key_type": "phone"
    }),
)
```
