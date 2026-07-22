from rest_framework import viewsets, permissions
from rest_framework.exceptions import ValidationError
from users.models import User
from .serializers import CustomerSerializer
from .models import Customer
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.CLIENTE:
            return Customer.objects.filter(user=user)
        return Customer.objects.all()

    def perform_create(self, serializer):
        requester = self.request.user
        if requester.role == User.Role.ADMIN:
            target_user_id = self.request.data.get("user")
            try:
                target_user = User.objects.get(pk=target_user_id)
            except User.DoesNotExist:
                raise ValidationError({"user": "Usuário informado não existe."})
            serializer.save(user=target_user)
        else:
            serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        if request.user.role == User.Role.CLIENTE:
            raise PermissionDenied("Clientes não podem desativar cadastros.")
        
        customer = self.get_object()
        customer.is_active = False
        customer.save()
        return Response(status=204)