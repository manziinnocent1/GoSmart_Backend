from django.db import transaction
from rest_framework import serializers

from accounts.validators import normalize_phone
from .models import PaymentMethod, PaymentTransaction


class PaymentMethodSerializer(serializers.ModelSerializer):
    masked_phone = serializers.SerializerMethodField()

    class Meta:
        model = PaymentMethod
        fields = ("id", "kind", "phone_number", "masked_phone", "is_default", "created_at")
        read_only_fields = ("id", "masked_phone", "is_default", "created_at")

    def validate(self, attrs):
        kind = attrs.get("kind", getattr(self.instance, "kind", None))
        phone = attrs.get("phone_number", getattr(self.instance, "phone_number", ""))
        if kind == PaymentMethod.Kind.CASH:
            attrs["phone_number"] = ""
            user = self.context["request"].user
            if not self.instance and user.payment_methods.filter(kind=kind).exists():
                raise serializers.ValidationError({"kind": "Cash is already saved as a payment method."})
        elif not phone:
            raise serializers.ValidationError(
                {"phone_number": "A mobile-money phone number is required."}
            )
        else:
            attrs["phone_number"] = normalize_phone(phone)
            local_number = f"0{attrs['phone_number'][4:]}"
            allowed = {
                PaymentMethod.Kind.MTN: {"078", "079"},
                PaymentMethod.Kind.AIRTEL: {"072", "073"},
            }
            if local_number[:3] not in allowed.get(kind, set()):
                raise serializers.ValidationError(
                    {"phone_number": f"The number prefix does not match the {kind} provider."}
                )
        return attrs

    def get_masked_phone(self, obj):
        if not obj.phone_number:
            return ""
        return f"{obj.phone_number[:4]}••••{obj.phone_number[-3:]}"

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user
        method, created = PaymentMethod.objects.get_or_create(
            user=user,
            kind=validated_data["kind"],
            phone_number=validated_data.get("phone_number", ""),
        )
        if not user.payment_methods.filter(is_default=True).exists():
            method.is_default = True
            method.save(update_fields=("is_default",))
        if not created:
            raise serializers.ValidationError({"phone_number": "This payment method already exists."})
        return method


class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = ("reference", "ride", "amount_rwf", "status", "provider_reference", "created_at")
        read_only_fields = fields
