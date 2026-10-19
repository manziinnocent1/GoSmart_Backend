from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AdminDashboardView,
    AdminDriverViewSet,
    AdminPricingViewSet,
    AdminSupportTicketViewSet,
    AdminSurgeZoneViewSet,
)

router = DefaultRouter()
router.register("drivers", AdminDriverViewSet, basename="admin-driver")
router.register("pricing", AdminPricingViewSet, basename="admin-pricing")
router.register("surge-zones", AdminSurgeZoneViewSet, basename="admin-surge-zone")
router.register("support/tickets", AdminSupportTicketViewSet, basename="admin-support-ticket")

urlpatterns = [
    path("dashboard/", AdminDashboardView.as_view(), name="admin-dashboard"),
    *router.urls,
]
