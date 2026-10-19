from rest_framework import serializers

from .models import PricingTier, SurgeZone


class PricingTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingTier
        fields = (
            "id",
            "vehicle_type",
            "display_name",
            "base_fare_rwf",
            "fare_per_km_rwf",
            "minimum_fare_rwf",
            "enabled",
            "updated_at",
        )
        read_only_fields = ("id", "updated_at")


class SurgeZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurgeZone
        fields = ("id", "name", "multiplier", "active", "latitude", "longitude", "radius_km", "updated_at")
        read_only_fields = ("id", "updated_at")
