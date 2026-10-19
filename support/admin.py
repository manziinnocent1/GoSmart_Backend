from django.contrib import admin

from .models import SupportMessage, SupportTicket


class SupportMessageInline(admin.TabularInline):
    model = SupportMessage
    extra = 0
    readonly_fields = ("sender", "body", "created_at")


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("reference", "customer", "title", "status", "updated_at")
    list_filter = ("status",)
    search_fields = ("reference", "title", "customer__email")
    inlines = (SupportMessageInline,)
