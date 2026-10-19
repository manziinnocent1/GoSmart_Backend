
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import SupportMessage, SupportTicket
from .serializers import (
    SupportMessageSerializer,
    SupportTicketCreateSerializer,
    SupportTicketSerializer,
)
from core.exceptions import Conflict

class SupportTicketViewSet(viewsets.ModelViewSet):
    http_method_names = ("get", "post", "head", "options")

    def get_queryset(self):
        return SupportTicket.objects.filter(customer=self.request.user).prefetch_related("messages")

    def get_serializer_class(self):
        return SupportTicketCreateSerializer if self.action == "create" else SupportTicketSerializer

    @action(detail=True, methods=("post",))
    def messages(self, request, pk=None):
        ticket = self.get_object()
        if ticket.status == SupportTicket.Status.SOLVED:
            raise Conflict("This support ticket is already closed.")
        body = request.data.get("body", "")
        if not isinstance(body, str) or not body.strip() or len(body) > 4000:
            raise ValidationError({"body": "Enter a message of 1 to 4,000 characters."})
        message = SupportMessage.objects.create(
            ticket=ticket, sender=request.user, body=body.strip()
        )
        ticket.save(update_fields=("updated_at",))
        return Response(SupportMessageSerializer(message).data, status=status.HTTP_201_CREATED)

