from django.contrib import admin

from .models import EmergencyAlert, SavedPlace


@admin.register(EmergencyAlert)
class EmergencyAlertAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "ride", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("user__email", "message")


admin.site.register(SavedPlace)
