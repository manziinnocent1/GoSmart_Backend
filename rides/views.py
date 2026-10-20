
from django.db import IntegrityError
from django.db.models import Avg
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from drivers.models import DriverProfile
from payments.models import PaymentMethod
from payments.serializers import PaymentTransactionSerializer
from payments.services import build_payment_transaction
from rides.matching import build_driver_offers
from rides.pins import issue_trip_pin
from rides.pricing import quote_fare
from .models import DriverRideOffer, Ride, RideRating
from .serializers import (
    FareQuoteInputSerializer,
    RideCreateSerializer,
    RideRatingSerializer,
    RideSerializer,
)
from core.exceptions import Conflict

class FareQuoteView(APIView):
    @extend_schema(
        request=FareQuoteInputSerializer,
        responses=OpenApiTypes.OBJECT,
    )
    def post(self, request):
        serializer = FareQuoteInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        quote = quote_fare(
            data["vehicle_type"], data["distance_km"], data.get("pickup_area", "")
        )
        return Response(
            {
                **quote,
                "pickup_label": data["pickup_label"],
                "destination_label": data["destination_label"],
                "duration_minutes": data["duration_minutes"],
            }
        )


class RideViewSet(viewsets.ModelViewSet):
    serializer_class = RideSerializer
    http_method_names = ("get", "post", "head", "options")

    def get_queryset(self):
        queryset = Ride.objects.select_related("driver__user", "payment_method", "passenger")
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(passenger=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = RideCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if Ride.objects.filter(
            passenger=request.user,
            status__in=(
                Ride.Status.SEARCHING,
                Ride.Status.ACCEPTED,
                Ride.Status.DRIVER_ARRIVING,
                Ride.Status.IN_PROGRESS,
            ),
        ).exists():
            raise Conflict("Finish or cancel your current ride before requesting another.")
        try:
            method = PaymentMethod.objects.get(
                pk=data["payment_method_id"], user=request.user
            )
        except PaymentMethod.DoesNotExist as exc:
            raise ValidationError({"payment_method_id": "Select one of your saved payment methods."}) from exc
        quote = quote_fare(
            data["vehicle_type"], data["distance_km"], data.get("pickup_area", "")
        )
        ride = Ride.objects.create(
            passenger=request.user,
            payment_method=method,
            vehicle_type=data["vehicle_type"],
            pickup_label=data["pickup_label"],
            destination_label=data["destination_label"],
            distance_km=data["distance_km"],
            duration_minutes=data["duration_minutes"],
            base_fare_rwf=quote["base_fare_rwf"],
            surge_multiplier=quote["surge_multiplier"],
            fare_rwf=quote["fare_rwf"],
            pickup_latitude=data.get("pickup_latitude"),
            pickup_longitude=data.get("pickup_longitude"),
            destination_latitude=data.get("destination_latitude"),
            destination_longitude=data.get("destination_longitude"),
        )
        build_driver_offers(ride)
        return Response(self.get_serializer(ride).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=("get",), url_path="trip-pin")
    def trip_pin(self, request, pk=None):
        ride = self.get_object()
        if ride.passenger_id != request.user.id:
            raise PermissionDenied("Only the passenger can retrieve the trip PIN.")
        if ride.status != Ride.Status.ACCEPTED:
            raise Conflict("A trip PIN is available after a driver accepts the ride.")
        return Response({"trip_pin": issue_trip_pin(ride)})

    @action(detail=True, methods=("post",))
    def cancel(self, request, pk=None):
        ride = self.get_object()
        if ride.passenger_id != request.user.id:
            raise PermissionDenied("Only the passenger who requested the ride can cancel it.")
        if ride.status not in (Ride.Status.SEARCHING, Ride.Status.ACCEPTED, Ride.Status.DRIVER_ARRIVING):
            raise Conflict("This ride can no longer be cancelled.")
        ride.status = Ride.Status.CANCELLED
        ride.cancellation_reason = str(request.data.get("reason", ""))[:240]
        ride.cancelled_by = request.user
        ride.cancelled_at = timezone.now()
        ride.save(update_fields=("status", "cancellation_reason", "cancelled_by", "cancelled_at"))
        ride.offers.filter(status=DriverRideOffer.Status.PENDING).update(
            status=DriverRideOffer.Status.EXPIRED, responded_at=timezone.now()
        )
        return Response(self.get_serializer(ride).data)

    @action(detail=True, methods=("post",))
    def arriving(self, request, pk=None):
        ride = Ride.objects.filter(pk=pk, driver=request.user.driver_profile).first()
        if not ride:
            raise NotFound("Ride not found.")
        if ride.status != Ride.Status.ACCEPTED:
            raise Conflict("Only an accepted ride can be marked as arriving.")
        ride.status = Ride.Status.DRIVER_ARRIVING
        ride.save(update_fields=("status",))
        return Response(self.get_serializer(ride).data)

    @action(detail=True, methods=("post",), url_path="payment-intent")
    def payment_intent(self, request, pk=None):
        ride = self.get_object()
        if ride.passenger_id != request.user.id:
            raise PermissionDenied("Only the passenger who requested the ride can pay for it.")
        try:
            payment = build_payment_transaction(ride)
        except APIException as exc:
            if exc.status_code == 503:
                ride.payment_status = Ride.PaymentStatus.FAILED
                ride.save(update_fields=("payment_status",))
                raise
            raise
        return Response(
            {
                "payment": PaymentTransactionSerializer(payment).data,
                "detail": "Payment is awaiting confirmation from the mobile-money provider.",
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=("post",))
    def rate(self, request, pk=None):
        ride = self.get_object()
        if ride.status != Ride.Status.COMPLETED:
            raise Conflict("A ride can be rated after it is completed.")
        if ride.passenger_id == request.user.id:
            target = ride.driver.user if ride.driver else None
        elif ride.driver_id and ride.driver.user_id == request.user.id:
            target = ride.passenger
        else:
            raise PermissionDenied("Only a passenger or driver on this ride can submit a rating.")
        if not target:
            raise Conflict("This ride has no assigned driver to rate.")
        rating_serializer = RideRatingSerializer(data=request.data)
        rating_serializer.is_valid(raise_exception=True)
        try:
            rating = RideRating.objects.create(
                ride=ride, rater=request.user, rated_user=target, **rating_serializer.validated_data
            )
        except IntegrityError as exc:
            raise Conflict("You have already rated this ride.") from exc
        if target.role == User.Role.DRIVER:
            average = RideRating.objects.filter(rated_user=target).aggregate(value=Avg("score"))["value"]
            DriverProfile.objects.filter(user=target).update(rating=average)
        return Response(
            {"score": rating.score, "comment": rating.comment},
            status=status.HTTP_201_CREATED,
        )
