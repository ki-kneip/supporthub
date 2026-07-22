from django.contrib import admin
from .models import Ticket

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("title", "customer", "category", "status", "priority", "assigned_to", "created_at", "updated_at")
    list_filter = ("status", "priority", "category", "assigned_to")
    ordering = ("-created_at",)