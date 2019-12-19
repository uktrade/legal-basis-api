Going to production
===================

This section covers everything you need to know before going to
production.

Django
------

### Checks

Before going to production make sure you have checked everything:

1.  Migrations are up-to-date
2.  Static files are all present
3.  There are no security or other `django` warnings

Checking migrations, static files, and security is done inside `ci.sh`
script.

We check that there are no unapplied migrations:

If you have forgotten to create a migration and changed the model, you
will see an error on this line.

We also check that static files can be collected:

However, this check does not cover all the cases. Sometimes
`ManifestStaticFilesStorage` will fail on real cases, but will pass with
`--dry-dun` option. You can disable `--dry-run` option if you know what
you are doing. Be careful with this option, when working with
auto-uploading your static files to any kind of CDNs.

That's how we check `django` warnings:

``` {.sourceCode .bash}
DJANGO_ENV=production python manage.py check --deploy --fail-level WARNING
```

These warnings are raised by `django` when it detects any configuration
issues.

This command should give not warnings or errors. It is bundled into
docker, so the container will not work with any warnings.

Further reading
---------------

-   Django's deployment
    [checklist](https://docs.djangoproject.com/en/dev/howto/deployment/checklist/#deployment-checklist)

