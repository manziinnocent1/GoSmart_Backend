from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from drivers.models import DriverProfile
from drivers.serializers import DriverProfileSerializer
from payments.models import PaymentMethod
from .models import User
from .validators import normalize_phone


class UserSerializer(serializers.ModelSerializer):
    driver_profile = DriverProfileSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "full_name",
            "first_name",
            "last_name",
            "phone_number",
            "role",
            "phone_verified",
            "preferred_language",
            "theme",
            "ride_notifications",
            "promotion_notifications",
            "driver_profile",
        )
        read_only_fields = ("id", "role", "phone_verified", "driver_profile")

    def get_full_name(self, obj):
        return obj.get_full_name()

    def validate_phone_number(self, value):
        normalized = normalize_phone(value)
        matches = User.objects.filter(phone_number=normalized)
        if self.instance:
            matches = matches.exclude(pk=self.instance.pk)
        if matches.exists():
            raise serializers.ValidationError("An account with this phone number already exists.")
        return normalized

    def update(self, instance, validated_data):
        phone_number = validated_data.get("phone_number")
        if phone_number is not None and phone_number != instance.phone_number:
            instance.phone_verified = False
        return super().update(instance, validated_data)


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    full_name = serializers.CharField(write_only=True, max_length=150)
    phone_number = serializers.CharField(max_length=20, required=True)
    vehicle_type = serializers.ChoiceField(
        choices=DriverProfile._meta.get_field("vehicle_type").choices,
        required=False,
        default="moto",
    )
    preferred_language = serializers.ChoiceField(
        choices=User._meta.get_field("preferred_language").choices,
        required=False,
        default="en",
    )

    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "full_name",
            "phone_number",
            "role",
            "vehicle_type",
            "preferred_language",
        )

    def validate_role(self, value):
        if value not in (User.Role.PASSENGER, User.Role.DRIVER):
            raise serializers.ValidationError(
                "Public registration is limited to passengers and drivers."
            )
        return value

    def validate_phone_number(self, value):
        normalized = normalize_phone(value)
        if User.objects.filter(phone_number=normalized).exists():
            raise serializers.ValidationError("An account with this phone number already exists.")
        return normalized

    @transaction.atomic
    def create(self, validated_data):
        full_name = validated_data.pop("full_name")
        vehicle_type = validated_data.pop("vehicle_type", "moto")
        name_parts = full_name.strip().split(maxsplit=1)
        user = User.objects.create_user(
            **validated_data,
            first_name=name_parts[0],
            last_name=name_parts[1] if len(name_parts) > 1 else "",
        )
        if user.role == User.Role.DRIVER:
            DriverProfile.objects.create(user=user, vehicle_type=vehicle_type)
        else:
            PaymentMethod.objects.create(user=user, kind=PaymentMethod.Kind.CASH, is_default=True)
        return user
