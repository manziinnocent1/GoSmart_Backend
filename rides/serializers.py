from decimal import Decimal

from rest_framework import serializers

from drivers.models import DriverProfile
from operations.models import PricingTier
from payments.serializers import PaymentMethodSerializer
from .models import Ride, RideRating


class FareQuoteInputSerializer(serializers.Serializer):
    vehicle_type = serializers.ChoiceField(choices=PricingTier._meta.get_field("vehicle_type").choices)
    pickup_label = serializers.CharField(max_length=160)
    destination_label = serializers.CharField(max_length=160)
    pickup_area = serializers.CharField(max_length=80, required=False, allow_blank=True)
    distance_km = serializers.DecimalField(
        max_digits=7, decimal_places=2, min_value=Decimal("0.1")
    )
    duration_minutes = serializers.IntegerField(min_value=1, max_value=240)
    pickup_latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    pickup_longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    destination_latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    destination_longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)


class RideCreateSerializer(serializers.Serializer):
    vehicle_type = serializers.ChoiceField(choices=PricingTier._meta.get_field("vehicle_type").choices)
    pickup_label = serializers.CharField(max_length=160)
    destination_label = serializers.CharField(max_length=160)
    pickup_area = serializers.CharField(max_length=80, required=False, allow_blank=True)
    distance_km = serializers.DecimalField(
        max_digits=7, decimal_places=2, min_value=Decimal("0.1")
    )
    duration_minutes = serializers.IntegerField(min_value=1, max_value=240)
    payment_method_id = serializers.UUIDField()
    pickup_latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    pickup_longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    destination_latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    destination_longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)


class DriverSummarySerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.get_full_name", read_only=True)
    phone = serializers.CharField(source="user.phone_number", read_only=True)
    vehicle = serializers.CharField(source="vehicle_model", read_only=True)
    color = serializers.CharField(source="vehicle_color", read_only=True)
    plate = serializers.CharField(source="license_plate", read_only=True)
    trips = serializers.IntegerField(source="completed_trips", read_only=True)

    class Meta:
        model = DriverProfile
        fields = ("id", "name", "phone", "vehicle_type", "vehicle", "color", "plate", "rating", "trips")


class RideSerializer(serializers.ModelSerializer):
    driver = DriverSummarySerializer(read_only=True)
    payment_method = PaymentMethodSerializer(read_only=True)
    passenger_name = serializers.CharField(source="passenger.get_full_name", read_only=True)

    class Meta:
        model = Ride
        fields = (
            "id",
            "reference",
            "passenger_name",
            "driver",
            "vehicle_type",
            "pickup_label",
            "destination_label",
            "pickup_latitude",
            "pickup_longitude",
            "destination_latitude",
            "destination_longitude",
            "distance_km",
            "duration_minutes",
            "base_fare_rwf",
            "surge_multiplier",
            "fare_rwf",
            "payment_method",
            "payment_status",
            "status",
            "requested_at",
            "accepted_at",
            "started_at",
            "completed_at",
            "cancelled_at",
        )
        read_only_fields = fields


class RideRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RideRating
        fields = ("score", "comment")
