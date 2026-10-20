import hashlib
import hmac
import json

from django.conf import settings
from django.db import transaction
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from rides.models import Ride
from .models import PaymentMethod, PaymentTransaction
from .serializers import PaymentMethodSerializer

class PaymentMethodViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentMethodSerializer

    def get_queryset(self):
        return PaymentMethod.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        if instance.is_default:
            replacement = self.get_queryset().exclude(pk=instance.pk).first()
            if replacement:
                replacement.is_default = True
                replacement.save(update_fields=("is_default",))
        instance.delete()

    @action(detail=True, methods=("post",), url_path="set-default")
    def set_default(self, request, pk=None):
        method = self.get_object()
        with transaction.atomic():
            PaymentMethod.objects.filter(user=request.user, is_default=True).update(is_default=False)
            method.is_default = True
            method.save(update_fields=("is_default",))
        return Response(self.get_serializer(method).data)


class PaymentProviderCallbackView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()

    @extend_schema(
        request=OpenApiTypes.OBJECT,
        responses=OpenApiTypes.OBJECT,
    )
    def post(self, request):
        signature = request.headers.get("X-GoSmart-Signature", "")
        expected = hmac.new(settings.MOMO_WEBHOOK_SECRET.encode(), request.body, hashlib.sha256).hexdigest()
        if not signature or not hmac.compare_digest(signature, expected):
            raise PermissionDenied("Invalid provider callback signature.")
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError as exc:
            raise ValidationError({"detail": "Invalid JSON callback."}) from exc
        reference = payload.get("reference")
        provider_status = payload.get("status")
        if provider_status not in ("succeeded", "failed"):
            raise ValidationError({"status": "Callback status must be succeeded or failed."})
        payment = PaymentTransaction.objects.select_related("ride").filter(reference=reference).first()
        if not payment:
            raise NotFound("Payment transaction not found.")
        if payment.status != PaymentTransaction.Status.PENDING:
            return Response({"detail": "Callback already processed."})
        payment.status = (
            PaymentTransaction.Status.SUCCEEDED
            if provider_status == "succeeded"
            else PaymentTransaction.Status.FAILED
        )
        payment.provider_reference = str(payload.get("provider_reference", ""))[:100]
        payment.save(update_fields=("status", "provider_reference", "updated_at"))
        payment.ride.payment_status = (
            Ride.PaymentStatus.PAID
            if provider_status == "succeeded"
            else Ride.PaymentStatus.FAILED
        )
        payment.ride.save(update_fields=("payment_status",))
        return Response({"detail": "Payment callback processed."})
