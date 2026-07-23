import os
import uuid

import redis
from celery import shared_task
from django.template.loader import render_to_string

from core.email import send_email

redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

def schedule_status_notification(ticket, countdown=30):
    token = uuid.uuid4().hex
    redis_client.set(f"ticket:{ticket.id}:status_token", token)
    notify_status_change.apply_async(args=[ticket.id, token], countdown=countdown)

@shared_task
def notify_status_change(ticket_id, token):
    latest = redis_client.get(f"ticket:{ticket_id}:status_token")
    if latest is None or latest.decode() != token:
        return  # uma mudanca mais recente ja assumiu

    from .models import Ticket
    ticket = Ticket.objects.get(id=ticket_id)

    html_content = render_to_string("emails/ticket_status_changed.html", {
        "customer_name": ticket.customer.name,
        "ticket_id": ticket.id,
        "ticket_title": ticket.title,
        "status_display": ticket.get_status_display(),
        "category_name": ticket.category.name,
        "priority_display": ticket.get_priority_display(),
    })

    send_email(
        to_email=ticket.customer.email,
        to_name=ticket.customer.name,
        subject=f"Chamado #{ticket.id} atualizado: {ticket.get_status_display()}",
        html_content=html_content,
    )
