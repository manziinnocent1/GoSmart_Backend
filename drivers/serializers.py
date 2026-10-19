from rest_framework import serializers

from .models import DriverCashout, DriverDocument, DriverProfile


class DriverDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverDocument
        fields = ("id", "kind", "status", "reference", "expires_at", "reviewed_at")
        read_only_fields = ("id", "status", "reviewed_at")


class DriverProfileSerializer(serializers.ModelSerializer):
    documents = DriverDocumentSerializer(many=True, read_only=True)
    driver_name = serializers.CharField(source="user.get_full_name", read_only=True)
    phone_number = serializers.CharField(source="user.phone_number", read_only=True)

    class Meta:
        model = DriverProfile
        fields = (
            "id",
            "driver_name",
            "phone_number",
            "vehicle_type",
            "vehicle_model",
            "vehicle_color",
            "license_plate",
            "payout_phone",
            "approval_status",
            "is_online",
            "accepts_cash",
            "rating",
            "completed_trips",
            "documents",
        )
        read_only_fields = (
            "id",
            "approval_status",
            "is_online",
            "rating",
            "completed_trips",
            "documents",
        )


class DriverCashoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverCashout
        fields = ("id", "amount_rwf", "payout_phone", "status", "provider_reference", "created_at")
        read_only_fields = ("id", "status", "provider_reference", "created_at")
