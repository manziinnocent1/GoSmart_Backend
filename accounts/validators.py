import re

from rest_framework import serializers


def normalize_phone(value):
    if not isinstance(value, str):
        raise serializers.ValidationError("Enter a valid Rwandan phone number.")
    digits = re.sub(r"\D", "", value)
    if digits.startswith("250") and len(digits) == 12:
        digits = f"0{digits[3:]}"
    if len(digits) != 10 or not digits.startswith("0"):
        raise serializers.ValidationError("Enter a valid Rwandan phone number.")
    return f"+250{digits[1:]}"
