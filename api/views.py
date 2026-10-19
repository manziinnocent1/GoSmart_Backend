"""Compatibility imports; HTTP behavior is implemented in feature apps."""

from accounts.views import AuthLoginView, AuthRegisterView, CurrentUserView, OtpRequestView, OtpVerifyView
from core.exceptions import Conflict
from core.views import EmergencyAlertViewSet, HealthView, SavedPlaceViewSet
from drivers.views import DriverCashoutViewSet, DriverDocumentViewSet, DriverEarningsView, DriverPreferencesView, DriverProfileView, DriverRequestViewSet
from operations.views import AdminDashboardView, AdminDriverViewSet, AdminPricingViewSet, AdminSupportTicketViewSet, AdminSurgeZoneViewSet
from payments.views import PaymentMethodViewSet, PaymentProviderCallbackView
from rides.views import FareQuoteView, RideViewSet
from support.views import SupportTicketViewSet

__all__ = [
    "AdminDashboardView", "AdminDriverViewSet", "AdminPricingViewSet",
    "AdminSupportTicketViewSet", "AdminSurgeZoneViewSet", "AuthLoginView",
    "AuthRegisterView", "Conflict", "CurrentUserView", "DriverCashoutViewSet",
    "DriverDocumentViewSet", "DriverEarningsView", "DriverPreferencesView",
    "DriverProfileView", "DriverRequestViewSet", "EmergencyAlertViewSet",
    "FareQuoteView", "HealthView", "OtpRequestView", "OtpVerifyView",
    "PaymentMethodViewSet", "PaymentProviderCallbackView", "RideViewSet",
    "SavedPlaceViewSet", "SupportTicketViewSet",
]
