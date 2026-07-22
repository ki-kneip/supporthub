from django.contrib import admin
from .models import Interaction

@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ("ticket", "author", "created_at")
    list_filter = ("ticket", "author", "created_at")
    ordering = ("-created_at",)