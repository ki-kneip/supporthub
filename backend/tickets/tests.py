import pytest
from django.urls import reverse
from rest_framework import status

from .models import Ticket

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