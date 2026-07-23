from unittest import mock

import pytest
from django.urls import reverse
from rest_framework import status

from . import tasks as tasks_module
from .models import Ticket
from .tasks import notify_status_change, schedule_status_notification

@pytest.mark.django_db
class TestTicketAPI:
    def test_cliente_cria_proprio_ticket(self, api_client, cliente_user, customer, category):
        api_client.force_authenticate(user=cliente_user)
        response = api_client.post(
            reverse("ticket-list"),
            {
                "title": "Erro no login",
                "description": "Não consigo logar na plataforma.",
                "category": category.id,
            },
            format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["customer"] == customer.id

    def test_cliente_nao_pode_definir_prioridade_na_criacao(self, api_client, cliente_user, category):
        api_client.force_authenticate(user=cliente_user)
        response = api_client.post(
            reverse("ticket-list"),
            {
                "title": "Erro no login",
                "description": "Não consigo logar na plataforma.",
                "category": category.id,
                "priority": Ticket.Priority.ALTA,  # Tentativa de definir prioridade
            },
            format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_admin_precisa_informar_customer(self, api_client, admin_user, category):
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            reverse("ticket-list"),
            {
                "title": "Erro no login",
                "description": "Não consigo logar na plataforma.",
                "category": category.id,
            },
            format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cliente_nao_ve_ticket_de_outro(self, api_client, ticket, admin_user):
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(reverse("ticket-detail", args=[ticket.id]))
        assert response.status_code == status.HTTP_200_OK

        from users.models import User

        # Criar outro cliente
        outro_cliente = User.objects.create_user(username="outro_cliente", password="123", role=User.Role.CLIENTE)
        api_client.force_authenticate(user=outro_cliente)
        response = api_client.get(reverse("ticket-detail", args=[ticket.id]))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_atendente_altera_status_do_ticket(self, api_client, atendente_user, ticket):
        api_client.force_authenticate(user=atendente_user)
        response = api_client.patch(
            reverse("ticket-detail", args=[ticket.id]),
            {"status": Ticket.Status.EM_ATENDIMENTO},
            format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        ticket.refresh_from_db()
        assert ticket.status == Ticket.Status.EM_ATENDIMENTO

    def test_cliente_nao_altera_status_do_ticket(self, api_client, cliente_user, ticket):
        api_client.force_authenticate(user=cliente_user)
        response = api_client.patch(
            reverse("ticket-detail", args=[ticket.id]),
            {"status": Ticket.Status.RESOLVIDO},
            format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestTicketStatusNotification:
    def test_mudar_status_dispara_notificacao(self, api_client, atendente_user, ticket):
        api_client.force_authenticate(user=atendente_user)
        with mock.patch("tickets.views.schedule_status_notification") as mock_schedule:
            response = api_client.patch(
                reverse("ticket-detail", args=[ticket.id]),
                {"status": Ticket.Status.EM_ATENDIMENTO},
                format="json",
            )

        assert response.status_code == status.HTTP_200_OK
        mock_schedule.assert_called_once()

    def test_atualizar_sem_mudar_status_nao_dispara_notificacao(self, api_client, atendente_user, ticket):
        api_client.force_authenticate(user=atendente_user)
        with mock.patch("tickets.views.schedule_status_notification") as mock_schedule:
            response = api_client.patch(
                reverse("ticket-detail", args=[ticket.id]),
                {"priority": Ticket.Priority.ALTA},
                format="json",
            )

        assert response.status_code == status.HTTP_200_OK
        mock_schedule.assert_not_called()

    def test_debounce_ignora_token_antigo_e_envia_com_o_mais_recente(self, ticket, monkeypatch):
        captured_tokens = []
        monkeypatch.setattr(
            tasks_module.notify_status_change,
            "apply_async",
            lambda args, countdown: captured_tokens.append(args[1]),
        )

        schedule_status_notification(ticket)
        schedule_status_notification(ticket)
        token_antigo, token_novo = captured_tokens

        with mock.patch("tickets.tasks.send_email") as mock_send:
            notify_status_change(ticket.id, token_antigo)
            assert not mock_send.called

            notify_status_change(ticket.id, token_novo)
            assert mock_send.called
            kwargs = mock_send.call_args.kwargs
            assert kwargs["to_email"] == ticket.customer.email
            assert str(ticket.id) in kwargs["subject"] or f"#{ticket.id}" in kwargs["subject"]