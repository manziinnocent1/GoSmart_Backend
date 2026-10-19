
from rest_framework import status, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .languages import SUPPORTED_LANGUAGES
from rides.models import Ride
from .models import EmergencyAlert, SavedPlace
from .serializers import EmergencyAlertCreateSerializer, SavedPlaceSerializer

class HealthView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        return Response({"status": "ok", "service": "GoSmart API", "version": "v1"})


class LanguagesView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        return Response(
            {
                "default": "en",
                "current": getattr(request, "LANGUAGE_CODE", "en"),
                "languages": SUPPORTED_LANGUAGES,
            }
        )


class SavedPlaceViewSet(viewsets.ModelViewSet):
    serializer_class = SavedPlaceSerializer

    def get_queryset(self):
        return SavedPlace.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class EmergencyAlertViewSet(viewsets.ModelViewSet):
    http_method_names = ("get", "post", "head", "options")

    def get_queryset(self):
        return EmergencyAlert.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = EmergencyAlertCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        ride = None
        ride_id = data.get("ride_id")
        if ride_id:
            ride = Ride.objects.filter(pk=ride_id, passenger=request.user).first()
            if not ride:
                raise NotFound("Active ride not found.")
        alert = EmergencyAlert.objects.create(
            user=request.user,
            ride=ride,
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            message=data.get("message", ""),
        )
        return Response(
            {
                "id": alert.id,
                "status": alert.status,
                "created_at": alert.created_at,
                "detail": "Emergency alert has been recorded.",
            },
            status=status.HTTP_201_CREATED,
        )
