from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.urls import include, path, re_path
from django.views.static import serve as media_serve


def healthz(_request):
    return HttpResponse("ok", content_type="text/plain")


def media_proxy(request, path):
    return media_serve(request, path, document_root=settings.MEDIA_ROOT)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("oauth/", include("allauth.urls")),
    path("healthz", healthz, name="healthz"),
    path("ops/", include("operations.urls")),
    path("", include("bookings.urls")),
]

if settings.MEDIA_URL.startswith("/") and not settings.GCS_MEDIA_BUCKET:
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", media_proxy),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
