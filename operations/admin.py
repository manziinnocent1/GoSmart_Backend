from django.contrib import admin

from .models import PricingTier, SurgeZone


@admin.register(PricingTier)
class PricingTierAdmin(admin.ModelAdmin):
    list_display = ("display_name", "vehicle_type", "base_fare_rwf", "fare_per_km_rwf", "enabled")
    list_filter = ("enabled", "vehicle_type")


@admin.register(SurgeZone)
class SurgeZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "multiplier", "active", "radius_km", "updated_at")
    list_filter = ("active",)
