from django.contrib import admin

from .models import PaymentMethod, PaymentTransaction


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ("user", "kind", "phone_number", "is_default", "created_at")
    list_filter = ("kind", "is_default")
    search_fields = ("user__email", "phone_number")


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("reference", "ride", "amount_rwf", "status", "provider_reference")
    list_filter = ("status",)
    readonly_fields = ("reference", "created_at", "updated_at")
