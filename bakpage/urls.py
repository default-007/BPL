"""bakpage URL Configuration"""

from django.conf import settings
from django.contrib import admin
from django.shortcuts import redirect
from django.templatetags.static import static
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    # Browsers request /favicon.ico directly, whatever the page links to.
    path("favicon.ico", lambda request: redirect(static("favicon.ico"))),
    path("", include("website.urls")),
    path("markdownx/", include("markdownx.urls")),
]

if settings.DEBUG or settings.SERVE_MEDIA:
    media_prefix = settings.MEDIA_URL.lstrip("/")
    urlpatterns += [
        re_path(
            rf"^{media_prefix}(?P<path>.*)$",
            serve,
            {"document_root": settings.MEDIA_ROOT},
        ),
    ]
