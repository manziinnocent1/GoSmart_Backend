"""Compatibility imports; serializer implementations live with their feature apps."""

from accounts.serializers import RegistrationSerializer, UserSerializer
from core.serializers import EmergencyAlertCreateSerializer, SavedPlaceSerializer
from drivers.serializers import (
    DriverCashoutSerializer,
    DriverDocumentSerializer,
    DriverProfileSerializer,
)
from operations.serializers import PricingTierSerializer, SurgeZoneSerializer
from payments.serializers import PaymentMethodSerializer, PaymentTransactionSerializer
from rides.serializers import (
    DriverSummarySerializer,
    FareQuoteInputSerializer,
    RideCreateSerializer,
    RideRatingSerializer,
    RideSerializer,
)
from support.serializers import (
    SupportMessageSerializer,
    SupportTicketCreateSerializer,
    SupportTicketSerializer,
)
from accounts.validators import normalize_phone

__all__ = [
    "DriverCashoutSerializer",
    "DriverDocumentSerializer",
    "DriverProfileSerializer",
    "DriverSummarySerializer",
    "EmergencyAlertCreateSerializer",
    "FareQuoteInputSerializer",
    "PaymentMethodSerializer",
    "PaymentTransactionSerializer",
    "PricingTierSerializer",
    "RegistrationSerializer",
    "RideCreateSerializer",
    "RideRatingSerializer",
    "RideSerializer",
    "SavedPlaceSerializer",
    "SupportMessageSerializer",
    "SupportTicketCreateSerializer",
    "SupportTicketSerializer",
    "SurgeZoneSerializer",
    "UserSerializer",
    "normalize_phone",
]
