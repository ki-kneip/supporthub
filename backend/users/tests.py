import pytest
from django.urls import reverse
from rest_framework import status

from .models import User


@pytest.mark.django_db
class TestUserMe:
    def test_cliente_ve_proprio_role_e_customer_id(self, api_client, cliente_user, customer):
        api_client.force_authenticate(user=cliente_user)
        response = api_client.get(reverse("user-me"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == cliente_user.id
        assert response.data["role"] == "cliente"
        assert response.data["customer_id"] == customer.id

    def test_atendente_sem_customer_recebe_null(self, api_client, atendente_user):
        api_client.force_authenticate(user=atendente_user)
        response = api_client.get(reverse("user-me"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["role"] == "atendente"
        assert response.data["customer_id"] is None

    def test_nao_autenticado_nao_acessa(self, api_client):
        response = api_client.get(reverse("user-me"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserAPI:
    def test_admin_lista_usuarios(self, api_client, admin_user, atendente_user):
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(reverse("user-list"))
        assert response.status_code == status.HTTP_200_OK

    def test_admin_filtra_por_role(self, api_client, admin_user, atendente_user, cliente_user):
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(reverse("user-list"), {"role": "atendente"})
        assert response.status_code == status.HTTP_200_OK
        roles = {u["role"] for u in response.data["results"]}
        assert roles == {"atendente"}

    def test_atendente_lista_usuarios(self, api_client, atendente_user):
        api_client.force_authenticate(user=atendente_user)
        response = api_client.get(reverse("user-list"))
        assert response.status_code == status.HTTP_200_OK

    def test_cliente_nao_lista_usuarios(self, api_client, cliente_user):
        api_client.force_authenticate(user=cliente_user)
        response = api_client.get(reverse("user-list"))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_cria_usuario(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            reverse("user-list"),
            {
                "username": "novo_atendente",
                "email": "novo@teste.com",
                "password": "senha123",
                "role": "atendente",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        created = User.objects.get(username="novo_atendente")
        assert created.role == "atendente"
        assert created.check_password("senha123")

    def test_atendente_nao_cria_usuario(self, api_client, atendente_user):
        api_client.force_authenticate(user=atendente_user)
        response = api_client.post(
            reverse("user-list"),
            {
                "username": "outro",
                "email": "outro@teste.com",
                "password": "senha123",
                "role": "cliente",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_altera_role_de_usuario(self, api_client, admin_user, cliente_user):
        api_client.force_authenticate(user=admin_user)
        response = api_client.patch(
            reverse("user-detail", args=[cliente_user.id]),
            {"role": "atendente"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        cliente_user.refresh_from_db()
        assert cliente_user.role == "atendente"

    def test_atendente_nao_altera_role(self, api_client, atendente_user, cliente_user):
        api_client.force_authenticate(user=atendente_user)
        response = api_client.patch(
            reverse("user-detail", args=[cliente_user.id]),
            {"role": "admin"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
