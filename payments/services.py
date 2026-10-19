import os

from rest_framework.exceptions import ValidationError

from core.providers import ProviderUnavailable, post_json
from rides.models import Ride

from .models import PaymentMethod, PaymentTransaction


def create_payment_request(payment, phone_number):
    provider_url = os.getenv("MOMO_PROVIDER_URL", "").strip()
    if not provider_url:
        raise ProviderUnavailable("Mobile-money payment processing is not configured.")
    response_data = post_json(
        provider_url,
        {
            "amount_rwf": payment.amount_rwf,
            "currency": "RWF",
            "phone_number": phone_number,
            "reference": str(payment.reference),
            "callback_url": (
                f"{os.getenv('PUBLIC_API_URL', '').rstrip('/')}"
                "/api/v1/payments/provider-callback/"
            ),
        },
        os.getenv("MOMO_PROVIDER_API_KEY", ""),
    )
    provider_reference = response_data.get("provider_reference")
    if not provider_reference:
        raise ProviderUnavailable("The payment provider response did not include a reference.")
    payment.provider_reference = str(provider_reference)[:100]
    payment.save(update_fields=("provider_reference", "updated_at"))


def build_payment_transaction(ride):
    method = ride.payment_method
    if not method or method.kind == PaymentMethod.Kind.CASH:
        raise ValidationError("A mobile-money payment method is required.")
    if ride.status != Ride.Status.ACCEPTED:
        raise ValidationError("Payment can only be requested after a driver accepts the ride.")
    if ride.payment_status == Ride.PaymentStatus.PAID:
        raise ValidationError("This ride has already been paid.")
    existing = ride.transactions.filter(status=PaymentTransaction.Status.PENDING).first()
    if existing:
        return existing
    payment = PaymentTransaction.objects.create(ride=ride, amount_rwf=ride.fare_rwf)
    try:
        create_payment_request(payment, method.phone_number)
    except ProviderUnavailable:
        payment.status = PaymentTransaction.Status.FAILED
        payment.save(update_fields=("status", "updated_at"))
        raise
    ride.payment_status = Ride.PaymentStatus.PENDING
    ride.save(update_fields=("payment_status",))
    return payment
