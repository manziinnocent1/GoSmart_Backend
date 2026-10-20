from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from importlib import import_module
from rest_framework.permissions import AllowAny

try:
    spectacular_views = import_module("drf_spectacular.views")
except ModuleNotFoundError as exc:
    if exc.name != "drf_spectacular":
        raise
    spectacular_views = None

def home(request):
    return JsonResponse({"message": "GoSmart API is running"})


def schema_unavailable(request):
    return JsonResponse(
        {"error": "API schema documentation is unavailable"}, status=503
    )


urlpatterns = [
    path('', home),
    path("django-admin/", admin.site.urls),
    path(
        "api/schema/",
        spectacular_views.SpectacularAPIView.as_view(permission_classes=[AllowAny])
        if spectacular_views
        else schema_unavailable,
        name="schema",
    ),
    path(
        "api/docs/",
        spectacular_views.SpectacularSwaggerView.as_view(url_name="schema")
        if spectacular_views
        else schema_unavailable,
        name="swagger-ui",
    ),
    path("api/v1/", include("core.urls")),
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/profile/", include("accounts.profile_urls")),
    path("api/v1/", include("rides.urls")),
    path("api/v1/payment-methods/", include("payments.urls")),
    path("api/v1/payments/provider-callback/", include("payments.callback_urls")),
    path("api/v1/driver/", include("drivers.urls")),
    path("api/v1/support/", include("support.urls")),
    path("api/v1/admin/", include("operations.urls")),
]
