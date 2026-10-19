from django.contrib import admin

from .models import DriverRideOffer, Ride, RideRating


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = ("reference", "passenger", "driver", "vehicle_type", "fare_rwf", "status", "requested_at")
    list_filter = ("status", "vehicle_type", "payment_status")
    search_fields = ("reference", "passenger__email", "driver__user__email")
    readonly_fields = ("reference", "requested_at", "accepted_at", "started_at", "completed_at")


admin.site.register((DriverRideOffer, RideRating))
