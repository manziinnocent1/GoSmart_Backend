import os

from django.conf import settings

from core.providers import ProviderUnavailable, post_json


def deliver_otp(phone_number, code):
    provider_url = os.getenv("SMS_PROVIDER_URL", "").strip()
    if provider_url:
        post_json(
            provider_url,
            {"to": phone_number, "message": f"Your GoSmart verification code is {code}."},
            os.getenv("SMS_PROVIDER_API_KEY", ""),
        )
        return False
    if settings.DEBUG and settings.OTP_EXPOSE_IN_DEBUG:
        return True
    raise ProviderUnavailable(
        "SMS delivery is not configured. Configure SMS_PROVIDER_URL or enable OTP_EXPOSE_IN_DEBUG locally."
    )
