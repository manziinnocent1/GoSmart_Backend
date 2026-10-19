from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    DriverCashoutViewSet,
    DriverDocumentViewSet,
    DriverEarningsView,
    DriverPreferencesView,
    DriverProfileView,
    DriverRequestViewSet,
)

router = DefaultRouter()
router.register("requests", DriverRequestViewSet, basename="driver-request")
router.register("cashouts", DriverCashoutViewSet, basename="driver-cashout")
router.register("documents", DriverDocumentViewSet, basename="driver-document")

urlpatterns = [
    path("profile/", DriverProfileView.as_view(), name="driver-profile"),
    path("preferences/", DriverPreferencesView.as_view(), name="driver-preferences"),
    path("earnings/", DriverEarningsView.as_view(), name="driver-earnings"),
    *router.urls,
]
