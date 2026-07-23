from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from core.permissions import IsAdminOrAtendente, IsAdminRole
from .models import User
from .serializers import (
    UserCreateSerializer,
    UserMeSerializer,
    UserRoleUpdateSerializer,
    UserSerializer,
)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("id")
    filterset_fields = ["role"]

    def get_serializer_class(self):
        if self.action == "me":
            return UserMeSerializer
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ("update", "partial_update"):
            return UserRoleUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == "me":
            return [permissions.IsAuthenticated()]
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdminRole()]
        return [IsAdminOrAtendente()]

    @action(detail=False, methods=["get"])
    def me(self, request):
        return Response(UserMeSerializer(request.user).data)