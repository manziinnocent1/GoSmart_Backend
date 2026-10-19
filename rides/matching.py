from django.utils import timezone

from drivers.models import DriverProfile
from payments.models import PaymentMethod

from .models import DriverRideOffer


def build_driver_offers(ride, exclude_driver_ids=()):
    eligible = DriverProfile.objects.filter(
        approval_status=DriverProfile.ApprovalStatus.APPROVED,
        is_online=True,
        vehicle_type=ride.vehicle_type,
    ).exclude(user_id__in=exclude_driver_ids)
    if ride.payment_method and ride.payment_method.kind == PaymentMethod.Kind.CASH:
        eligible = eligible.filter(accepts_cash=True)
    existing = set(ride.offers.values_list("driver_id", flat=True))
    DriverRideOffer.objects.bulk_create(
        [
            DriverRideOffer(ride=ride, driver=driver)
            for driver in eligible
            if driver.id not in existing
        ],
        ignore_conflicts=True,
    )


def notify_online_driver_of_waiting_rides(driver):
    if not driver.is_online or driver.approval_status != DriverProfile.ApprovalStatus.APPROVED:
        return
    from .models import Ride

    rides = Ride.objects.filter(
        status=Ride.Status.SEARCHING, vehicle_type=driver.vehicle_type
    ).exclude(offers__driver=driver)
    if not driver.accepts_cash:
        rides = rides.exclude(payment_method__kind=PaymentMethod.Kind.CASH)
    DriverRideOffer.objects.bulk_create(
        [DriverRideOffer(ride=ride, driver=driver) for ride in rides],
        ignore_conflicts=True,
    )
