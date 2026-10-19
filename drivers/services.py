from decimal import Decimal

from django.db.models import Sum

from payments.models import PaymentMethod
from rides.models import Ride

from .models import DriverCashout, DriverProfile


def wallet_balance(driver):
    rides = Ride.objects.filter(driver=driver, status=Ride.Status.COMPLETED).select_related("payment_method")
    momo_net = sum(
        int(ride.fare_rwf * Decimal("0.85"))
        for ride in rides
        if ride.payment_method and ride.payment_method.kind != PaymentMethod.Kind.CASH
    )
    cash_commission = sum(
        int(ride.fare_rwf * Decimal("0.15"))
        for ride in rides
        if ride.payment_method and ride.payment_method.kind == PaymentMethod.Kind.CASH
    )
    cashouts = DriverCashout.objects.filter(
        driver=driver,
        status__in=(
            DriverCashout.Status.PENDING,
            DriverCashout.Status.PROCESSING,
            DriverCashout.Status.PAID,
        ),
    ).aggregate(total=Sum("amount_rwf"))["total"] or 0
    return max(0, momo_net - cash_commission - cashouts)
