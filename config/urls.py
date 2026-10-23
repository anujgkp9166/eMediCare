from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("", include("care.urls")),
    path("", include("diagnostics.urls")),
    path("", include("core.urls")),
    # Public media (doctor photos). Patient reports are NOT served from here.
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]

handler404 = "core.views.not_found"
