import uuid

from django.conf import settings
from django.db import models


class PaymentMethod(models.Model):
    class Kind(models.TextChoices):
        CASH = "cash", "Cash"
        MTN = "mtn", "MTN MoMo"
        AIRTEL = "airtel", "Airtel Money"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_methods")
    kind = models.CharField(max_length=8, choices=Kind.choices)
    phone_number = models.CharField(max_length=20, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "kind", "phone_number"),
                condition=~models.Q(kind="cash"),
                name="unique_wallet_number_per_user",
            )
        ]
        ordering = ("-is_default", "created_at")


class PaymentTransaction(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    reference = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ride = models.ForeignKey("rides.Ride", on_delete=models.PROTECT, related_name="transactions")
    amount_rwf = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    provider_reference = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
