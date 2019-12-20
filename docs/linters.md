Linters
=======

This project uses several linters to make coding style consistent. All
configuration is stored inside `setup.cfg`.

wemake-python-styleguide
------------------------

`wemake-python-styleguide` is a `flake8` based plugin. And it is also
the strictest and most opinionated python linter ever. See
[wemake-python-styleguide](https://wemake-python-styleguide.readthedocs.io/en/latest/)
docs.

Things that are included in the linting process:

-   [flake8](http://flake8.pycqa.org/) is used a general tool for
    linting
-   [isort](https://github.com/timothycrosley/isort) is used to validate
    `import` order
-   [bandit](https://github.com/PyCQA/bandit) for static security checks
-   [eradicate](https://github.com/myint/eradicate) to find dead code
-   and more!

Running linting process for all `python` files in the project:

``` {.sourceCode .bash}
flake8 .
```

### Extra plugins

We also use some extra plugins for `flake8` that are not bundled with
`wemake-python-styleguide`:

-   [flake8-pytest](https://github.com/vikingco/flake8-pytest) - ensures
    that `pytest` best practices are used
-   [flake8-pytest-style](https://github.com/m-burst/flake8-pytest-style) -
    ensures that `pytest` tests and fixtures are written in a single
    style
-   [flake8-django](https://github.com/rocioar/flake8-django) - plugin
    to enforce best practices in a `django` project

xenon
-----

We are also using [xenon](https://github.com/rubik/xenon) to measure
code complexity and quality.

Here are our standards:

-   A single block of code can not go below `A` mark
-   A single module can not go below `A` mark
-   Overall mark cannot go below `A` mark

If your commit breaks this rule: well, the build won't succeed.

``` {.sourceCode .bash}
xenon --max-absolute A --max-modules A --max-average A server
```

It will return status code `0` if everything is fine.

django-migration-linter
-----------------------

We use `django-migration-linter` to find backward incompatible
migrations. It allows us to write 0-downtime friendly code.

See
[django-migration-linter](https://github.com/3YOURMIND/django-migration-linter)
docs, it contains a lot of useful information about ways and tools to do
it.

That's how this check is executed:

``` {.sourceCode .bash}
python manage.py lintmigrations --exclude-apps=axes
```

Important note: you might want to exclude some packages with broken
migrations. Sometimes, there's nothing we can do about it.

yamllint
--------

Is used to lint your `yaml` files. See
[yamllint](https://github.com/adrienverge/yamllint) docs.

``` {.sourceCode .bash}
yamllint -d '{"extends": "default", "ignore": ".venv"}' -s .
```

dotenv-linter
-------------

Is used to lint your `.env` files. See
[dotenv-linter](https://github.com/wemake-services/dotenv-linter) docs.

``` {.sourceCode .bash}
dotenv-linter config/.env config/.env.template
```

Packaging
---------

We also use `pip` and `poetry` self checks to be sure that packaging
works correctly.

``` {.sourceCode .bash}
poetry check && pip check
```
