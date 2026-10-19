import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.choices import VehicleType


class Ride(models.Model):
    class Status(models.TextChoices):
        SEARCHING = "searching", "Searching for driver"
        ACCEPTED = "accepted", "Driver assigned"
        DRIVER_ARRIVING = "driver_arriving", "Driver arriving"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", "Unpaid"
        PENDING = "pending", "Payment pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Payment failed"
        REFUNDED = "refunded", "Refunded"

    reference = models.CharField(max_length=12, unique=True, editable=False)
    passenger = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="rides")
    driver = models.ForeignKey(
        "drivers.DriverProfile", on_delete=models.PROTECT, related_name="rides", null=True, blank=True
    )
    vehicle_type = models.CharField(max_length=8, choices=VehicleType.choices)
    pickup_label = models.CharField(max_length=160)
    destination_label = models.CharField(max_length=160)
    pickup_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    pickup_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    destination_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    destination_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    distance_km = models.DecimalField(max_digits=7, decimal_places=2)
    duration_minutes = models.PositiveSmallIntegerField()
    base_fare_rwf = models.PositiveIntegerField()
    surge_multiplier = models.DecimalField(max_digits=3, decimal_places=1, default=1)
    fare_rwf = models.PositiveIntegerField()
    payment_method = models.ForeignKey(
        "payments.PaymentMethod", on_delete=models.SET_NULL, null=True, blank=True, related_name="rides"
    )
    payment_status = models.CharField(
        max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SEARCHING)
    start_pin_hash = models.CharField(max_length=128, blank=True)
    cancellation_reason = models.CharField(max_length=240, blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="cancelled_rides"
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-requested_at",)
        indexes = [
            models.Index(fields=("passenger", "status")),
            models.Index(fields=("driver", "status")),
            models.Index(fields=("status", "requested_at")),
        ]

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"GS{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.reference


class DriverRideOffer(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        EXPIRED = "expired", "Expired"

    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name="offers")
    driver = models.ForeignKey(
        "drivers.DriverProfile", on_delete=models.CASCADE, related_name="ride_offers"
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    offered_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("ride", "driver"), name="one_offer_per_driver_per_ride")
        ]
        indexes = [models.Index(fields=("driver", "status", "offered_at"))]


class RideRating(models.Model):
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name="ratings")
    rater = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="given_ratings")
    rated_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="received_ratings")
    score = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("ride", "rater", "rated_user"), name="one_rating_per_user_per_ride")
        ]
