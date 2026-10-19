from rest_framework import serializers

from .models import SavedPlace


class SavedPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedPlace
        fields = ("id", "label", "address", "latitude", "longitude", "created_at")
        read_only_fields = ("id", "created_at")


class EmergencyAlertCreateSerializer(serializers.Serializer):
    ride_id = serializers.IntegerField(required=False)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    message = serializers.CharField(max_length=240, required=False, allow_blank=True)
