# Django Rest Framework (same as datahub-api)

REST_FRAMEWORK = {
    'UNAUTHENTICATED_USER': None,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'hawkrest.HawkAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100,
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly',
    ],
    'ORDERING_PARAM': 'sortby',
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}
# Hawkrest
HAWK_USER_LOOKUP = 'server.apps.main.auth.hawk_user_lookup'
HAWK_CREDENTIALS_LOOKUP = 'server.apps.main.auth.hawk_credentials_lookup'
