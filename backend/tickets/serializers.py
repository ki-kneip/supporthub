from customers.models import Customer
from rest_framework import serializers
from .models import Ticket
from users.models import User

class TicketSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all(), required=False)

    category_name = serializers.CharField(source="category.name", read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    assigned_to_username = serializers.CharField(
        source="assigned_to.username",
        read_only=True,
        default=None,
    )

    class Meta:
        model = Ticket
        fields = [
            "id",
            "title",
            "description",
            "customer",
            "customer_name",
            "category",
            "category_name",
            "status",
            "priority",
            "assigned_to",
            "assigned_to_username",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    RESTRICTED_FIELDS = {"status", "priority", "assigned_to"}
    def validate(self, attrs):
        request = self.context.get("request")
        if request:
            if request.user.role == User.Role.CLIENTE:
                touched = self.RESTRICTED_FIELDS & set(attrs.keys())
                if touched:
                    raise serializers.ValidationError(
                        {
                            field: "Você não tem permissão para definir este campo." 
                            for field in touched
                        }
                    )
            elif self.instance is None and "customer" not in attrs:
                raise serializers.ValidationError(
                    {"customer": "Obrigatório informar o cliente."}
                )
        return attrs