from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("django-admin/", admin.site.urls),
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
