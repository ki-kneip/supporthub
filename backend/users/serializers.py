from customers.models import Customer
from rest_framework import serializers
from .models import User

class UserMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "customer_id"]

    customer_id = serializers.SerializerMethodField()

    def get_customer_id(self, obj) -> int | None:
        customer = Customer.objects.filter(user=obj).first()
        return customer.id if customer else None


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "is_active"]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "role"]

    def create(self, validated_data):
        role = validated_data.get("role", User.Role.CLIENTE)
        is_admin = role == User.Role.ADMIN
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
            role=role,
            is_staff=is_admin,
            is_superuser=is_admin,
        )


class UserRoleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "role"]
        read_only_fields = ["id"]

    def update(self, instance, validated_data):
        role = validated_data.get("role", instance.role)
        instance.role = role
        instance.is_staff = role == User.Role.ADMIN
        instance.is_superuser = role == User.Role.ADMIN
        instance.save()
        return instance