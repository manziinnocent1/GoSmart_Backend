import csv
from datetime import timedelta

from django.db.models import Avg, Count, Sum
from django.http import HttpResponse
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drivers.models import DriverDocument, DriverProfile
from drivers.serializers import DriverDocumentSerializer, DriverProfileSerializer
from operations.models import PricingTier, SurgeZone
from operations.permissions import IsStaffAdmin
from operations.serializers import PricingTierSerializer, SurgeZoneSerializer
from rides.models import Ride
from support.models import SupportMessage, SupportTicket
from support.serializers import SupportMessageSerializer, SupportTicketSerializer
from core.exceptions import Conflict

class AdminDashboardView(APIView):
    permission_classes = (IsAuthenticated, IsStaffAdmin)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        now = timezone.now()
        today = timezone.localdate()
        completed_today = Ride.objects.filter(status=Ride.Status.COMPLETED, completed_at__date=today)
        metrics = {
            "active_rides": Ride.objects.filter(
                status__in=(Ride.Status.ACCEPTED, Ride.Status.DRIVER_ARRIVING, Ride.Status.IN_PROGRESS)
            ).count(),
            "online_vehicles": DriverProfile.objects.filter(
                is_online=True, approval_status=DriverProfile.ApprovalStatus.APPROVED
            ).count(),
            "average_eta_minutes": round(
                Ride.objects.filter(status=Ride.Status.ACCEPTED).aggregate(
                    value=Avg("duration_minutes")
                )["value"]
                or 0,
                1,
            ),
            "revenue_today_rwf": completed_today.aggregate(value=Sum("fare_rwf"))["value"] or 0,
            "open_support_tickets": SupportTicket.objects.exclude(
                status=SupportTicket.Status.SOLVED
            ).count(),
            "pending_driver_approvals": DriverProfile.objects.filter(
                approval_status=DriverProfile.ApprovalStatus.PENDING
            ).count(),
            "generated_at": now,
        }
        if request.query_params.get("format") == "csv":
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="gosmart-operations.csv"'
            writer = csv.writer(response)
            writer.writerow(("metric", "value"))
            writer.writerows(metrics.items())
            return response
        weekly = []
        for offset in range(6, -1, -1):
            day = today - timedelta(days=offset)
            revenue = Ride.objects.filter(
                status=Ride.Status.COMPLETED, completed_at__date=day
            ).aggregate(value=Sum("fare_rwf"))["value"] or 0
            weekly.append({"date": day, "revenue_rwf": revenue})
        demand = list(
            Ride.objects.filter(requested_at__date=today)
            .values("vehicle_type")
            .annotate(requests=Count("id"))
            .order_by("vehicle_type")
        )
        return Response({**metrics, "weekly_revenue": weekly, "demand_by_vehicle": demand})


class AdminDriverViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DriverProfileSerializer
    permission_classes = (IsAuthenticated, IsStaffAdmin)
    search_fields = ("user__first_name", "user__last_name", "user__phone_number", "license_plate", "vehicle_model")
    filterset_fields = ("approval_status", "vehicle_type", "is_online")
    queryset = DriverProfile.objects.select_related("user").prefetch_related("documents").all()

    @action(detail=True, methods=("post",))
    def approve(self, request, pk=None):
        driver = self.get_object()
        required = {
            DriverDocument.Kind.LICENSE,
            DriverDocument.Kind.NATIONAL_ID,
            DriverDocument.Kind.INSURANCE,
        }
        verified = set(
            driver.documents.filter(status=DriverDocument.Status.VERIFIED).values_list("kind", flat=True)
        )
        missing = sorted(required - verified)
        if missing:
            raise ValidationError(
                {"documents": f"Required documents must be verified first: {', '.join(missing)}."}
            )
        driver.approval_status = DriverProfile.ApprovalStatus.APPROVED
        driver.save(update_fields=("approval_status", "updated_at"))
        return Response(self.get_serializer(driver).data)

    @action(detail=True, methods=("post",))
    def reject(self, request, pk=None):
        driver = self.get_object()
        driver.approval_status = DriverProfile.ApprovalStatus.REJECTED
        driver.is_online = False
        driver.save(update_fields=("approval_status", "is_online", "updated_at"))
        return Response(self.get_serializer(driver).data)

    @action(
        detail=True,
        methods=("post",),
        url_path=r"documents/(?P<document_id>[^/.]+)/review",
    )
    def review_document(self, request, pk=None, document_id=None):
        driver = self.get_object()
        document = driver.documents.filter(pk=document_id).first()
        if not document:
            raise NotFound("Driver document not found.")
        new_status = request.data.get("status")
        valid_statuses = (DriverDocument.Status.VERIFIED, DriverDocument.Status.REJECTED)
        if new_status not in valid_statuses:
            raise ValidationError({"status": "Choose verified or rejected."})
        document.status = new_status
        document.reviewed_at = timezone.now()
        document.save(update_fields=("status", "reviewed_at"))
        return Response(DriverDocumentSerializer(document).data)


class AdminPricingViewSet(viewsets.ModelViewSet):
    serializer_class = PricingTierSerializer
    permission_classes = (IsAuthenticated, IsStaffAdmin)
    queryset = PricingTier.objects.all()
    http_method_names = ("get", "post", "patch", "put", "head", "options")


class AdminSurgeZoneViewSet(viewsets.ModelViewSet):
    serializer_class = SurgeZoneSerializer
    permission_classes = (IsAuthenticated, IsStaffAdmin)
    queryset = SurgeZone.objects.all()
    http_method_names = ("get", "post", "patch", "put", "delete", "head", "options")


class AdminSupportTicketViewSet(viewsets.ModelViewSet):
    serializer_class = SupportTicketSerializer
    permission_classes = (IsAuthenticated, IsStaffAdmin)
    queryset = SupportTicket.objects.select_related("customer", "ride").prefetch_related("messages")
    filterset_fields = ("status",)
    search_fields = ("reference", "title", "customer__email", "customer__first_name", "customer__last_name")
    http_method_names = ("get", "patch", "head", "options")

    def partial_update(self, request, *args, **kwargs):
        ticket = self.get_object()
        new_status = request.data.get("status")
        if new_status and new_status not in SupportTicket.Status.values:
            raise ValidationError({"status": "Choose urgent, open, or solved."})
        if new_status:
            ticket.status = new_status
            ticket.save(update_fields=("status", "updated_at"))
        return Response(self.get_serializer(ticket).data)

    @action(detail=True, methods=("post",))
    def reply(self, request, pk=None):
        ticket = self.get_object()
        if ticket.status == SupportTicket.Status.SOLVED:
            raise Conflict("Reopen the support ticket before replying.")
        body = request.data.get("body", "")
        if not isinstance(body, str) or not body.strip() or len(body) > 4000:
            raise ValidationError({"body": "Enter a message of 1 to 4,000 characters."})
        message = SupportMessage.objects.create(
            ticket=ticket, sender=request.user, body=body.strip()
        )
        ticket.save(update_fields=("updated_at",))
        return Response(SupportMessageSerializer(message).data, status=status.HTTP_201_CREATED)
