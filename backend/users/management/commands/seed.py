import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from categories.models import Category
from customers.models import Customer
from users.models import User

CATEGORIES = [
    ("Erro no sistema", "Falhas, bugs e comportamentos inesperados no sistema."),
    ("Solicitacao de acesso", "Pedidos de acesso a sistemas, permissoes ou recursos."),
    ("Problema financeiro", "Questoes relacionadas a cobranca, pagamento ou faturamento."),
    ("Suporte tecnico", "Duvidas ou problemas tecnicos gerais de uso."),
    ("Duvida geral", "Perguntas gerais que nao se encaixam nas demais categorias."),
]

CLIENTES = [
    ("cliente1", "Ana Souza", "ana.souza@example.com", "11988887777"),
    ("cliente2", "Bruno Lima", "bruno.lima@example.com", "11977776666"),
    ("cliente3", "Carla Mendes", "carla.mendes@example.com", "11966665555"),
]


class Command(BaseCommand):
    help = "Popula o banco com dados iniciais: admin, atendente, categorias e clientes de exemplo."

    def _resolve_password(self):
        password = os.getenv("SEED_PASSWORD")
        if password:
            return password

        if settings.DEBUG:
            self.stdout.write(self.style.WARNING(
                "SEED_PASSWORD nao definida; usando senha padrao insegura (permitido so com DEBUG=True)."
            ))
            return "supporthub123"

        raise CommandError(
            "SEED_PASSWORD precisa ser definida no ambiente quando DEBUG=False (producao)."
        )

    def _create_user(self, username, email, role, password, is_admin=False):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "role": role,
                "is_staff": is_admin,
                "is_superuser": is_admin,
            },
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Usuario '{username}' criado (role={role})."))
        else:
            self.stdout.write(f"Usuario '{username}' ja existe, pulando.")
        return user

    def handle(self, *args, **options):
        password = self._resolve_password()

        self._create_user("admin", "admin@supporthub.com", User.Role.ADMIN, password, is_admin=True)
        self._create_user("atendente1", "atendente1@supporthub.com", User.Role.ATENDENTE, password)

        for name, description in CATEGORIES:
            _, created = Category.objects.get_or_create(
                name=name, defaults={"description": description}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Categoria '{name}' criada."))
            else:
                self.stdout.write(f"Categoria '{name}' ja existe, pulando.")

        for username, full_name, email, phone in CLIENTES:
            user = self._create_user(username, email, User.Role.CLIENTE, password)

            _, created = Customer.objects.get_or_create(
                user=user,
                defaults={"name": full_name, "email": email, "phone": phone},
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Cliente '{full_name}' ({username}) criado."))
            else:
                self.stdout.write(f"Cliente '{full_name}' ja existe, pulando.")

        self.stdout.write(self.style.SUCCESS("Seed concluido."))
