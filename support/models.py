import uuid

from django.conf import settings
from django.db import models


class SupportTicket(models.Model):
    class Status(models.TextChoices):
        URGENT = "urgent", "Urgent"
        OPEN = "open", "Open"
        SOLVED = "solved", "Solved"

    reference = models.CharField(max_length=12, unique=True, editable=False)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="support_tickets"
    )
    ride = models.ForeignKey(
        "rides.Ride", on_delete=models.SET_NULL, null=True, blank=True, related_name="support_tickets"
    )
    title = models.CharField(max_length=160)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"TR{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)


class SupportMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="support_messages"
    )
    body = models.TextField(max_length=4000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
