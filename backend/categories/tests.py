import pytest
from django.urls import reverse
from rest_framework import status

from .models import Category

@pytest.mark.django_db
class TestCategoryAPI:
    def test_admin_pode_criar_categoria(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            reverse("category-list"),
            {"name": "Nova Categoria"},
            format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Category.objects.filter(name="Nova Categoria").exists()

    def test_cliente_nao_pode_criar_categoria(self, api_client, cliente_user):
        api_client.force_authenticate(user=cliente_user)
        response = api_client.post(
            reverse("category-list"),
            {"name": "Tentativa Cliente"},
            format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cliente_pode_listar_categorias(self, api_client, cliente_user, category):
        api_client.force_authenticate(user=cliente_user)
        response = api_client.get(reverse("category-list"))
        assert response.status_code == status.HTTP_200_OK
        assert any(cat["name"] == category.name for cat in response.data["results"])

    def test_anonimo_nao_pode_listar(self, api_client):
        response = api_client.get(reverse("category-list"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED