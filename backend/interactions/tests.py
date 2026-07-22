import pytest
from django.urls import reverse
from rest_framework import status

from .models import Interaction


@pytest.mark.django_db
class TestInteractionAPI:
    def test_cliente_registra_interacao_no_proprio_ticket(self, api_client, cliente_user, ticket):
        api_client.force_authenticate(user=cliente_user)
        response = api_client.post(
            reverse("ticket-interactions", args=[ticket.id]),
            {
                "message": "Ainda estou com problemas.",
            },
            format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["author"] == cliente_user.id

    def test_cliente_lista_interacoes_do_proprio_ticket(self, api_client, cliente_user, ticket):
        Interaction.objects.create(ticket=ticket, author=cliente_user, message="Primeira mensagem")

        api_client.force_authenticate(user=cliente_user)
        response = api_client.get(reverse("ticket-interactions", args=[ticket.id]))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["message"] == "Primeira mensagem"

    def test_admin_lista_interacoes_de_qualquer_ticket(self, api_client, admin_user, cliente_user, ticket):
        Interaction.objects.create(ticket=ticket, author=cliente_user, message="Mensagem do cliente")
        Interaction.objects.create(ticket=ticket, author=admin_user, message="Resposta do atendimento")

        api_client.force_authenticate(user=admin_user)
        response = api_client.get(reverse("ticket-interactions", args=[ticket.id]))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_cliente_nao_lista_interacoes_de_ticket_alheio(self, api_client, ticket):
        from users.models import User

        estranho = User.objects.create_user(username="estranho2", password="123", role=User.Role.CLIENTE)

        api_client.force_authenticate(user=estranho)
        response = api_client.get(reverse("ticket-interactions", args=[ticket.id]))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_mensagem_e_obrigatoria(self, api_client, cliente_user, ticket):
        api_client.force_authenticate(user=cliente_user)
        response = api_client.post(
            reverse("ticket-interactions", args=[ticket.id]),
            {},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "message" in response.data

    def test_interacoes_retornadas_em_ordem_cronologica(self, api_client, admin_user, cliente_user, ticket):
        primeira = Interaction.objects.create(ticket=ticket, author=cliente_user, message="Primeira")
        segunda = Interaction.objects.create(ticket=ticket, author=admin_user, message="Segunda")
        terceira = Interaction.objects.create(ticket=ticket, author=cliente_user, message="Terceira")

        api_client.force_authenticate(user=admin_user)
        response = api_client.get(reverse("ticket-interactions", args=[ticket.id]))

        assert response.status_code == status.HTTP_200_OK
        ids_na_ordem = [item["id"] for item in response.data]
        assert ids_na_ordem == [primeira.id, segunda.id, terceira.id]
