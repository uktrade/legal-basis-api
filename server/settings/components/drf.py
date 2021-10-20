# Django Rest Framework (same as datahub-api)

REST_FRAMEWORK = {
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "server.apps.main.auth.HawkUserAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 100,
    "DEFAULT_PERMISSION_CLASSES": [
        "server.apps.main.permissions.LegalBasisModelPermissions",
    ],
    "ORDERING_PARAM": "sortby",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}
