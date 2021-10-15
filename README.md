# legal_basis_api

[![Maintainability](https://api.codeclimate.com/v1/badges/39311945e75aa22cc954/maintainability)](https://codeclimate.com/github/uktrade/legal-basis-api/maintainability) [![Test Coverage](https://api.codeclimate.com/v1/badges/39311945e75aa22cc954/test_coverage)](https://codeclimate.com/github/uktrade/legal-basis-api/test_coverage)

Allows DIT's services to set and retrieve marketing consent settings for their users.

## Architecture

![Architecture Diagram](docs/diagrams/DIT%20Consent%20architecture.png?raw=true)
[SVG](docs/diagrams/DIT%20Consent%20architecture.svg?raw=true) | [Visio](docs/diagrams/DIT%20Consent%20architecture.vsdx?raw=true)

## Documentation

Full documentation is available here: [`docs/`](docs), which includes a [Postman collection](docs/Consent%20Service.postman_collection.json).

## Prerequisites

You will need:

- `python3.7`
- `postgresql` with version `11.6`
- `docker` with [version at least](https://docs.docker.com/compose/compose-file/#compose-and-docker-compatibility-matrix) `18.02`

## Running locally

To start development with `docker` you will need to create a local `.env` file based on the sample provided:

```{.sourceCode .bash}
cp config/sample.env config/.env
```

You will then need to ask a team member for the sso credentials and update the `AUTHBROKER_*` values in 
the newly created`.env` file.

Now you are ready to build and bring up the django app.

``` {.sourceCode .bash}
docker-compose build
docker-compose run --rm web python manage.py migrate
docker-compose run --rm web python manage.py collectstatic
docker-compose up
```

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
        "phone": "+442071838750",  # In E.164 format
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
        "phone": "+442071838750",  # In E.164 format
        "key_type": "phone",
    }),
)
```
