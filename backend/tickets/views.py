from interactions.serializers import InteractionSerializer
from .serializers import TicketSerializer
from users.models import User
from .models import Ticket
from customers.models import Customer
from rest_framework import viewsets, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["status", "priority", "category", "customer", "assigned_to"]
    search_fields = ["title", "description"]

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.CLIENTE:
            return Ticket.objects.filter(customer__user=user)
        return Ticket.objects.all()

    def perform_create(self, serializer):
        requester = self.request.user
        if requester.role == User.Role.CLIENTE:
            try:
                customer = Customer.objects.get(user=requester)
            except Customer.DoesNotExist:
                raise ValidationError({"customer": "Cliente não encontrado para o usuário."})
            serializer.save(customer=customer)
        else:
            serializer.save()

    @action(detail=True, methods=["get", "post"])
    def interactions(self, request, pk=None):
        ticket = self.get_object()

        if request.method == "GET":
            serializer = InteractionSerializer(ticket.interactions.all(), many=True)
            return Response(serializer.data)

        serializer = InteractionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(ticket=ticket, author=request.user)
        return Response(serializer.data, status=201)