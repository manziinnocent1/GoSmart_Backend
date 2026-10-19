from decimal import Decimal

from rest_framework.test import APITestCase

from accounts.models import User
from drivers.models import DriverProfile
from operations.models import PricingTier
from payments.models import PaymentMethod
from .models import DriverRideOffer, Ride


class RideApiTests(APITestCase):
    def setUp(self):
        PricingTier.objects.create(
            vehicle_type="moto",
            display_name="Moto",
            base_fare_rwf=500,
            fare_per_km_rwf=400,
            minimum_fare_rwf=700,
        )
        self.passenger = User.objects.create_user(
            email="rider@example.com",
            password="SafePassphrase2026!",
            first_name="Aline",
            role=User.Role.PASSENGER,
            phone_number="+250788123456",
        )
        self.cash = PaymentMethod.objects.create(
            user=self.passenger,
            kind=PaymentMethod.Kind.CASH,
            is_default=True,
        )
        self.driver_user = User.objects.create_user(
            email="driver@example.com",
            password="SafePassphrase2026!",
            first_name="Jean Paul",
            role=User.Role.DRIVER,
            phone_number="+250788987654",
        )
        self.driver = DriverProfile.objects.create(
            user=self.driver_user,
            vehicle_type="moto",
            approval_status=DriverProfile.ApprovalStatus.APPROVED,
            is_online=True,
        )

    def test_fare_quote_uses_persisted_pricing(self):
        self.client.force_authenticate(self.passenger)
        response = self.client.post(
            "/api/v1/fares/quote/",
            {
                "vehicle_type": "moto",
                "pickup_label": "Kimironko",
                "destination_label": "Kigali Heights",
                "distance_km": "4.80",
                "duration_minutes": 14,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["fare_rwf"], 2400)

    def test_driver_accepts_and_completes_cash_ride_with_passenger_pin(self):
        ride = Ride.objects.create(
            passenger=self.passenger,
            payment_method=self.cash,
            vehicle_type="moto",
            pickup_label="Kimironko",
            destination_label="Kigali Heights",
            distance_km=Decimal("4.80"),
            duration_minutes=14,
            base_fare_rwf=2400,
            fare_rwf=2400,
        )
        DriverRideOffer.objects.create(ride=ride, driver=self.driver)

        self.client.force_authenticate(self.driver_user)
        accepted = self.client.post(f"/api/v1/driver/requests/{ride.pk}/accept/", {}, format="json")
        self.assertEqual(accepted.status_code, 200, accepted.data)
        self.assertEqual(accepted.data["ride"]["status"], Ride.Status.ACCEPTED)

        self.client.force_authenticate(self.passenger)
        pin_response = self.client.get(f"/api/v1/rides/{ride.pk}/trip-pin/")
        self.assertEqual(pin_response.status_code, 200, pin_response.data)
        pin = pin_response.data["trip_pin"]

        self.client.force_authenticate(self.driver_user)
        started = self.client.post(
            f"/api/v1/driver/requests/{ride.pk}/start/", {"pin": pin}, format="json"
        )
        self.assertEqual(started.status_code, 200, started.data)
        self.assertEqual(started.data["status"], Ride.Status.IN_PROGRESS)
        completed = self.client.post(f"/api/v1/driver/requests/{ride.pk}/complete/", {}, format="json")
        self.assertEqual(completed.status_code, 200, completed.data)
        self.assertEqual(completed.data["status"], Ride.Status.COMPLETED)
        self.assertEqual(completed.data["payment_status"], Ride.PaymentStatus.PAID)
