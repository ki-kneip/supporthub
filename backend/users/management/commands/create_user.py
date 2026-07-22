import getpass

from django.core.management.base import BaseCommand, CommandError

from users.models import User


class Command(BaseCommand):
    help = "Cria um usuario com um perfil (role) especifico: cliente, atendente ou admin."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--email", default="")
        parser.add_argument(
            "--role",
            choices=[User.Role.CLIENTE, User.Role.ATENDENTE, User.Role.ADMIN],
            default=User.Role.CLIENTE,
        )
        parser.add_argument(
            "--password",
            default=None,
            help="Se omitido, a senha e' pedida de forma segura (sem aparecer no terminal).",
        )

    def handle(self, *args, **options):
        username = options["username"]
        email = options["email"]
        role = options["role"]
        password = options["password"] or getpass.getpass("Senha: ")

        if User.objects.filter(username=username).exists():
            raise CommandError(f"Usuario '{username}' ja existe.")

        is_admin = role == User.Role.ADMIN

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            is_staff=is_admin,
            is_superuser=is_admin,
        )

        self.stdout.write(self.style.SUCCESS(
            f"Usuario '{user.username}' criado com role='{user.role}' "
            f"(is_staff={user.is_staff}, is_superuser={user.is_superuser})."
        ))
