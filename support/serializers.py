from rest_framework import serializers

from .models import SupportMessage, SupportTicket


class SupportMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.get_full_name", read_only=True)

    class Meta:
        model = SupportMessage
        fields = ("id", "sender", "sender_name", "body", "created_at")
        read_only_fields = ("id", "sender", "sender_name", "created_at")


class SupportTicketSerializer(serializers.ModelSerializer):
    messages = SupportMessageSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="customer.get_full_name", read_only=True)

    class Meta:
        model = SupportTicket
        fields = (
            "id",
            "reference",
            "customer_name",
            "ride",
            "title",
            "status",
            "messages",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "reference",
            "customer_name",
            "status",
            "messages",
            "created_at",
            "updated_at",
        )


class SupportTicketCreateSerializer(serializers.ModelSerializer):
    initial_message = serializers.CharField(max_length=4000, write_only=True)

    class Meta:
        model = SupportTicket
        fields = ("ride", "title", "initial_message")

    def create(self, validated_data):
        initial_message = validated_data.pop("initial_message")
        user = self.context["request"].user
        ticket = SupportTicket.objects.create(customer=user, **validated_data)
        SupportMessage.objects.create(ticket=ticket, sender=user, body=initial_message)
        return ticket
