from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.choices import VehicleType


class PricingTier(models.Model):
    vehicle_type = models.CharField(max_length=8, choices=VehicleType.choices, unique=True)
    display_name = models.CharField(max_length=40)
    base_fare_rwf = models.PositiveIntegerField()
    fare_per_km_rwf = models.PositiveIntegerField()
    minimum_fare_rwf = models.PositiveIntegerField(default=500)
    enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name


class SurgeZone(models.Model):
    name = models.CharField(max_length=80, unique=True)
    multiplier = models.DecimalField(
        max_digits=3, decimal_places=1, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    active = models.BooleanField(default=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    radius_km = models.PositiveSmallIntegerField(default=3)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.multiplier}x)"
