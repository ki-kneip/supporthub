import pytest
from rest_framework.test import APIClient
from users.models import User
from categories.models import Category
from customers.models import Customer
from tickets.models import Ticket

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(username="admin_test", password="123", role=User.Role.ADMIN)


@pytest.fixture
def atendente_user(db):
    return User.objects.create_user(username="atendente_test", password="123", role=User.Role.ATENDENTE)


@pytest.fixture
def cliente_user(db):
    return User.objects.create_user(username="cliente_test", password="123", role=User.Role.CLIENTE)


@pytest.fixture
def category(db):
    return Category.objects.create(name="Categoria Teste")


@pytest.fixture
def customer(db, cliente_user):
    return Customer.objects.create(user=cliente_user, name="Cliente Teste", email="cliente@teste.com")

@pytest.fixture
def ticket(db, customer, category):
    return Ticket.objects.create(
        title="Ticket Teste", description="Descrição", customer=customer, category=category
    )
