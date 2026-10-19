from decimal import Decimal, ROUND_HALF_UP

from rest_framework.exceptions import NotFound

from operations.models import PricingTier, SurgeZone


def quote_fare(vehicle_type, distance_km, pickup_area=""):
    try:
        tier = PricingTier.objects.get(vehicle_type=vehicle_type, enabled=True)
    except PricingTier.DoesNotExist as exc:
        raise NotFound("This ride type is currently unavailable.") from exc
    raw_fare = Decimal(tier.base_fare_rwf) + tier.fare_per_km_rwf * Decimal(distance_km)
    base_fare = max(
        tier.minimum_fare_rwf,
        int((raw_fare / Decimal(50)).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * 50),
    )
    surge = Decimal("1.0")
    zone = None
    if vehicle_type != "moto" and pickup_area:
        zone = SurgeZone.objects.filter(active=True, name__iexact=pickup_area).first()
        if zone:
            surge = zone.multiplier
    fare = int(
        (Decimal(base_fare) * surge / Decimal(50)).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
        * 50
    )
    return {
        "vehicle_type": vehicle_type,
        "display_name": tier.display_name,
        "distance_km": Decimal(distance_km),
        "base_fare_rwf": base_fare,
        "surge_multiplier": surge,
        "surge_zone": zone.name if zone else None,
        "fare_rwf": fare,
    }
