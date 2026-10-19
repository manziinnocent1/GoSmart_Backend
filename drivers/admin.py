from django.contrib import admin

from .models import DriverCashout, DriverDocument, DriverProfile


class DriverDocumentInline(admin.TabularInline):
    model = DriverDocument
    extra = 0


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "vehicle_type", "license_plate", "approval_status", "is_online", "rating")
    list_filter = ("approval_status", "vehicle_type", "is_online")
    search_fields = ("user__email", "user__phone_number", "license_plate", "vehicle_model")
    inlines = (DriverDocumentInline,)


@admin.register(DriverCashout)
class DriverCashoutAdmin(admin.ModelAdmin):
    list_display = ("driver", "amount_rwf", "status", "payout_phone", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)
