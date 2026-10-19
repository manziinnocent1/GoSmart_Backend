from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import EmergencyAlertViewSet, HealthView, LanguagesView, SavedPlaceViewSet

router = DefaultRouter()
router.register("saved-places", SavedPlaceViewSet, basename="saved-place")
router.register("emergency-alerts", EmergencyAlertViewSet, basename="emergency-alert")

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("languages/", LanguagesView.as_view(), name="languages"),
    *router.urls,
]
