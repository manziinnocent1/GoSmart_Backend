from django.conf import settings
from django.db import models

from core.choices import VehicleType


class DriverProfile(models.Model):
    class ApprovalStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        SUSPENDED = "suspended", "Suspended"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="driver_profile"
    )
    vehicle_type = models.CharField(max_length=8, choices=VehicleType.choices)
    vehicle_model = models.CharField(max_length=100, blank=True)
    vehicle_color = models.CharField(max_length=40, blank=True)
    license_plate = models.CharField(max_length=20, unique=True, null=True, blank=True)
    payout_phone = models.CharField(max_length=20, blank=True)
    approval_status = models.CharField(
        max_length=12, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING
    )
    is_online = models.BooleanField(default=False)
    accepts_cash = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5)
    completed_trips = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.vehicle_type})"


class DriverDocument(models.Model):
    class Kind(models.TextChoices):
        LICENSE = "license", "Driving licence"
        NATIONAL_ID = "national_id", "National ID"
        INSURANCE = "insurance", "Insurance"
        INSPECTION = "inspection", "Vehicle inspection"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"
        EXPIRING = "expiring", "Expiring"

    driver = models.ForeignKey(DriverProfile, on_delete=models.CASCADE, related_name="documents")
    kind = models.CharField(max_length=20, choices=Kind.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    reference = models.CharField(max_length=100, blank=True)
    expires_at = models.DateField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("driver", "kind"), name="one_document_per_driver_kind")
        ]


class DriverCashout(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"

    driver = models.ForeignKey(DriverProfile, on_delete=models.PROTECT, related_name="cashouts")
    amount_rwf = models.PositiveIntegerField()
    payout_phone = models.CharField(max_length=20)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    provider_reference = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
