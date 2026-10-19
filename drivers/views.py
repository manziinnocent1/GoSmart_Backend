
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from payments.models import PaymentMethod
from rides.matching import build_driver_offers, notify_online_driver_of_waiting_rides
from rides.models import DriverRideOffer, Ride
from rides.pins import verify_trip_pin
from rides.serializers import RideSerializer
from .models import DriverCashout, DriverProfile
from .permissions import IsDriver, IsDriverAccount
from .serializers import DriverCashoutSerializer, DriverDocumentSerializer, DriverProfileSerializer
from .services import wallet_balance as driver_wallet_balance
from core.exceptions import Conflict

class DriverRequestViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RideSerializer
    permission_classes = (IsAuthenticated, IsDriver)

    def get_queryset(self):
        driver = self.request.user.driver_profile
        return (
            Ride.objects.filter(
                offers__driver=driver,
                offers__status=DriverRideOffer.Status.PENDING,
                status=Ride.Status.SEARCHING,
            )
            .select_related("passenger", "payment_method")
            .distinct()
        )

    @action(detail=True, methods=("post",))
    def accept(self, request, pk=None):
        with transaction.atomic():
            ride = Ride.objects.select_for_update().filter(pk=pk).first()
            if not ride or ride.status != Ride.Status.SEARCHING:
                raise NotFound("This ride request is no longer available.")
            offer = DriverRideOffer.objects.select_for_update().filter(
                ride=ride,
                driver=request.user.driver_profile,
                status=DriverRideOffer.Status.PENDING,
            ).first()
            if not offer:
                raise NotFound("This ride request is no longer available.")
            ride.driver = request.user.driver_profile
            ride.status = Ride.Status.ACCEPTED
            ride.accepted_at = timezone.now()
            ride.save(update_fields=("driver", "status", "accepted_at"))
            offer.status = DriverRideOffer.Status.ACCEPTED
            offer.responded_at = timezone.now()
            offer.save(update_fields=("status", "responded_at"))
            ride.offers.exclude(pk=offer.pk).filter(status=DriverRideOffer.Status.PENDING).update(
                status=DriverRideOffer.Status.EXPIRED, responded_at=timezone.now()
            )
        ride = Ride.objects.select_related("driver__user", "payment_method", "passenger").get(pk=ride.pk)
        return Response({"ride": RideSerializer(ride).data})

    @action(detail=True, methods=("post",))
    def decline(self, request, pk=None):
        offer = DriverRideOffer.objects.filter(
            ride_id=pk,
            driver=request.user.driver_profile,
            status=DriverRideOffer.Status.PENDING,
        ).first()
        if not offer:
            raise NotFound("This ride request is no longer available.")
        offer.status = DriverRideOffer.Status.DECLINED
        offer.responded_at = timezone.now()
        offer.save(update_fields=("status", "responded_at"))
        return Response({"detail": "Ride request declined."})

    @action(detail=True, methods=("post",))
    def start(self, request, pk=None):
        ride = Ride.objects.filter(pk=pk, driver=request.user.driver_profile).first()
        if not ride:
            raise NotFound("Ride not found.")
        if ride.status not in (Ride.Status.ACCEPTED, Ride.Status.DRIVER_ARRIVING):
            raise Conflict("Only an accepted ride can be started.")
        pin = str(request.data.get("pin", ""))
        if len(pin) != 4 or not pin.isdigit() or not verify_trip_pin(ride, pin):
            raise ValidationError({"pin": "The trip PIN is incorrect."})
        if ride.payment_method and ride.payment_method.kind != PaymentMethod.Kind.CASH:
            if ride.payment_status != Ride.PaymentStatus.PAID:
                raise Conflict("The passenger's mobile-money payment is not confirmed yet.")
        ride.status = Ride.Status.IN_PROGRESS
        ride.started_at = timezone.now()
        ride.save(update_fields=("status", "started_at"))
        return Response(self.get_serializer(ride).data)

    @action(detail=True, methods=("post",))
    def complete(self, request, pk=None):
        with transaction.atomic():
            ride = Ride.objects.select_for_update().filter(
                pk=pk, driver=request.user.driver_profile
            ).first()
            if not ride:
                raise NotFound("Ride not found.")
            if ride.status != Ride.Status.IN_PROGRESS:
                raise Conflict("Only an in-progress ride can be completed.")
            if ride.payment_method and ride.payment_method.kind == PaymentMethod.Kind.CASH:
                ride.payment_status = Ride.PaymentStatus.PAID
            ride.status = Ride.Status.COMPLETED
            ride.completed_at = timezone.now()
            ride.driver.completed_trips += 1
            ride.driver.save(update_fields=("completed_trips", "updated_at"))
            ride.save(update_fields=("status", "payment_status", "completed_at"))
        return Response(self.get_serializer(ride).data)

    @action(detail=True, methods=("post",))
    def cancel(self, request, pk=None):
        with transaction.atomic():
            ride = Ride.objects.select_for_update().filter(
                pk=pk, driver=request.user.driver_profile
            ).first()
            if not ride:
                raise NotFound("Ride not found.")
            if ride.status not in (Ride.Status.ACCEPTED, Ride.Status.DRIVER_ARRIVING):
                raise Conflict("This ride can no longer be cancelled by the driver.")
            old_driver_id = ride.driver_id
            ride.driver = None
            ride.status = Ride.Status.SEARCHING
            ride.accepted_at = None
            ride.save(update_fields=("driver", "status", "accepted_at"))
            ride.offers.filter(
                driver_id=old_driver_id, status=DriverRideOffer.Status.ACCEPTED
            ).update(status=DriverRideOffer.Status.DECLINED, responded_at=timezone.now())
            build_driver_offers(ride, exclude_driver_ids=(request.user.id,))
        return Response({"detail": "Ride returned to the driver matching queue."})


class DriverPreferencesView(APIView):
    permission_classes = (IsAuthenticated, IsDriver)

    def patch(self, request):
        profile = request.user.driver_profile
        if "accepts_cash" in request.data:
            profile.accepts_cash = serializers.BooleanField().run_validation(
                request.data["accepts_cash"]
            )
        if "is_online" in request.data:
            profile.is_online = serializers.BooleanField().run_validation(request.data["is_online"])
        profile.save(update_fields=("accepts_cash", "is_online", "updated_at"))
        notify_online_driver_of_waiting_rides(profile)
        return Response(DriverProfileSerializer(profile).data)


class DriverProfileView(APIView):
    permission_classes = (IsAuthenticated, IsDriverAccount)

    def get(self, request):
        return Response(DriverProfileSerializer(request.user.driver_profile).data)

    def patch(self, request):
        serializer = DriverProfileSerializer(
            request.user.driver_profile, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class DriverDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DriverDocumentSerializer
    permission_classes = (IsAuthenticated, IsDriverAccount)
    http_method_names = ("get", "post", "patch", "head", "options")

    def get_queryset(self):
        return self.request.user.driver_profile.documents.all()

    def perform_create(self, serializer):
        serializer.save(driver=self.request.user.driver_profile)


class DriverEarningsView(APIView):
    permission_classes = (IsAuthenticated, IsDriver)

    def get(self, request):
        driver = request.user.driver_profile
        trips = Ride.objects.filter(driver=driver, status=Ride.Status.COMPLETED)
        today = timezone.localdate()
        today_trips = trips.filter(completed_at__date=today)
        trip_rows = [
            {
                "id": ride.reference,
                "kind": "trip",
                "when": ride.completed_at,
                "pickup": ride.pickup_label,
                "destination": ride.destination_label,
                "vehicle_type": ride.vehicle_type,
                "fare_rwf": ride.fare_rwf,
                "commission_rwf": round(ride.fare_rwf * 0.15),
                "net_earnings_rwf": ride.fare_rwf - round(ride.fare_rwf * 0.15),
                "payment_kind": ride.payment_method.kind if ride.payment_method else None,
            }
            for ride in trips[:50]
        ]
        cashouts = [
            {
                "id": cashout.id,
                "kind": "cashout",
                "when": cashout.created_at,
                "amount_rwf": cashout.amount_rwf,
                "status": cashout.status,
            }
            for cashout in driver.cashouts.all()[:20]
        ]
        history = sorted(trip_rows + cashouts, key=lambda row: row["when"], reverse=True)
        return Response(
            {
                "wallet_balance_rwf": driver_wallet_balance(driver),
                "earnings_today_rwf": sum(
                    ride.fare_rwf - round(ride.fare_rwf * 0.15) for ride in today_trips
                ),
                "trips_today": today_trips.count(),
                "completed_trips": trips.count(),
                "commission_rate": "0.15",
                "history": history,
            }
        )


class DriverCashoutViewSet(viewsets.ModelViewSet):
    serializer_class = DriverCashoutSerializer
    permission_classes = (IsAuthenticated, IsDriver)
    http_method_names = ("get", "post", "head", "options")

    def get_queryset(self):
        return DriverCashout.objects.filter(driver=self.request.user.driver_profile)

    def create(self, request, *args, **kwargs):
        driver = request.user.driver_profile
        if not driver.payout_phone:
            raise ValidationError({"payout_phone": "Add a mobile-money payout number to your driver profile."})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data["amount_rwf"]
        if amount < 1000:
            raise ValidationError({"amount_rwf": "The minimum cash-out is RWF 1,000."})
        with transaction.atomic():
            DriverProfile.objects.select_for_update().get(pk=driver.pk)
            balance = driver_wallet_balance(driver)
            if amount > balance:
                raise ValidationError({"amount_rwf": "The requested cash-out exceeds your available balance."})
            cashout = DriverCashout.objects.create(
                driver=driver,
                amount_rwf=amount,
                payout_phone=driver.payout_phone,
            )
        return Response(
            {
                **self.get_serializer(cashout).data,
                "detail": "Cash-out request recorded and awaiting payout-provider processing.",
            },
            status=status.HTTP_202_ACCEPTED,
        )
