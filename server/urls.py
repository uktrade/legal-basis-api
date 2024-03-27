"""
Main URL mapping configuration file.

Include other URLConfs from external apps using method `include()`.

It is also a good practice to keep a single URL to the root index page.

This examples uses Django's default media
files serving technique in development.
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from health_check import urls as health_urls

from server.apps.api import urls as api_urls
from server.apps.main.feeds import W3CModelJSONActivityFeed

admin.autodiscover()


urlpatterns = [
    # Apps:
    path("api/v1/", include(api_urls, namespace="v1")),
    # Admin Export:
    path("admin-export/", include('server.apps.admin_export.urls')),
    # Health checks:
    path("health/", include(health_urls)),  # noqa: DJ05
    # Django Admin Oauth2
    path("admin/auth/", include("authbroker_client.urls")),
    # django-admin:
    path("admin/", admin.site.urls),
    # activitystream
    path(
        "activity/feed/<int:content_type_id>/json/",
        W3CModelJSONActivityFeed.as_view(),
        name="actstream_model_feed_json",
    ),
    # Text and xml static files:
    path(
        "robots.txt",
        TemplateView.as_view(
            template_name="txt/robots.txt", content_type="text/plain",
        ),
    ),
]

if settings.DEBUG:  # pragma: no cover
    import debug_toolbar  # noqa: WPS433
    from django.conf.urls.static import static  # noqa: WPS433

    urlpatterns = (
        [
            # URLs specific only to django-debug-toolbar:
            path("__debug__/", include(debug_toolbar.urls)),  # noqa: DJ05
        ]
        + urlpatterns
        + static(
            # Serving media files in development only:
            settings.MEDIA_URL,
            document_root=settings.MEDIA_ROOT,
        )
    )
