from django.core.management.base import BaseCommand

from operations.models import PricingTier, SurgeZone


class Command(BaseCommand):
    help = "Create GoSmart's initial ride tiers and sample Kigali surge zones."

    def handle(self, *args, **options):
        tiers = (
            ("moto", "Moto", 500, 400, 700),
            ("car", "Car Comfort", 1200, 800, 1500),
            ("xl", "XL Van", 2000, 1200, 2500),
        )
        for vehicle_type, name, base_fare, per_km, minimum in tiers:
            PricingTier.objects.update_or_create(
                vehicle_type=vehicle_type,
                defaults={
                    "display_name": name,
                    "base_fare_rwf": base_fare,
                    "fare_per_km_rwf": per_km,
                    "minimum_fare_rwf": minimum,
                    "enabled": True,
                },
            )
        for name, multiplier in (("Remera", "1.5"), ("Downtown", "1.2")):
            SurgeZone.objects.update_or_create(
                name=name,
                defaults={"multiplier": multiplier, "active": True},
            )
        self.stdout.write(self.style.SUCCESS("Initial fare tiers and surge zones are ready."))
