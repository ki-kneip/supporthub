from django.conf import settings
from django.db import models

class Interaction(models.Model):
    class Meta:
        ordering = ["created_at"]

    ticket = models.ForeignKey("tickets.Ticket", on_delete=models.CASCADE, related_name="interactions")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="interactions")
    message = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author} - {self.ticket_id}"