from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FareQuoteView, RideViewSet

router = DefaultRouter()
router.register("rides", RideViewSet, basename="ride")

urlpatterns = [
    path("fares/quote/", FareQuoteView.as_view(), name="fare-quote"),
    *router.urls,
]
