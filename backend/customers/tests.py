import pytest
from django.urls import reverse
from rest_framework import status

from .models import Customer

@pytest.mark.django_db
class TestCustomerAPI:
    def test_cliente_cria_proprio_cadastro(self, api_client, cliente_user):
        api_client.force_authenticate(user=cliente_user)
        response = api_client.post(
            reverse("customer-list"),
            {
                "name": "Novo Cliente",
                "email": "fulano@teste.com",
                "phone": "123456789",
            },
            format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["user"] == cliente_user.id

    def test_admin_cria_cadastro_para_outro_usuario(self, api_client, admin_user, cliente_user):
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            reverse("customer-list"),
            {
                "user": cliente_user.id,
                "name": "Fulano",
                "email": "fulano@teste.com",
                "phone": "123456789",
            },
            format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["user"] == cliente_user.id

    def test_admin_com_usuario_inexistente_da_erro(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            reverse("customer-list"),
            {
                "user": 9999,  # ID de usuário inexistente
                "name": "Fulano",
                "email": "fulano@teste.com",
                "phone": "123456789",
            },
            format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cliente_nao_ve_customer_de_outro(self, api_client, cliente_user, customer, admin_user):
        outro_customer = Customer.objects.create(
            user=admin_user, name="Outro", email="outro@teste.com"
        )
        api_client.force_authenticate(user=cliente_user)
        response = api_client.get(reverse("customer-detail", args=[outro_customer.id]))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cliente_nao_pode_desativar(self, api_client, cliente_user, customer):
        api_client.force_authenticate(user=cliente_user)
        response = api_client.delete(reverse("customer-detail", args=[customer.id]))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_desativa_customer(self, api_client, admin_user, customer):
        api_client.force_authenticate(user=admin_user)
        response = api_client.delete(reverse("customer-detail", args=[customer.id]))
        assert response.status_code == status.HTTP_204_NO_CONTENT

        customer.refresh_from_db()
        assert customer.is_active is False

