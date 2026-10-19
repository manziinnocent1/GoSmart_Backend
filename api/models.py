"""Backward-compatible imports for the feature-owned Django models.

New model definitions belong in their feature app, not in this API package.
"""

from accounts.models import PhoneVerification, User, UserManager
from core.models import EmergencyAlert, SavedPlace
from drivers.models import DriverCashout, DriverDocument, DriverProfile
from operations.models import PricingTier, SurgeZone
from payments.models import PaymentMethod, PaymentTransaction
from rides.models import DriverRideOffer, Ride, RideRating
from support.models import SupportMessage, SupportTicket

__all__ = [
    "DriverCashout",
    "DriverDocument",
    "DriverProfile",
    "DriverRideOffer",
    "EmergencyAlert",
    "PaymentMethod",
    "PaymentTransaction",
    "PhoneVerification",
    "PricingTier",
    "Ride",
    "RideRating",
    "SavedPlace",
    "SupportMessage",
    "SupportTicket",
    "SurgeZone",
    "User",
    "UserManager",
]
