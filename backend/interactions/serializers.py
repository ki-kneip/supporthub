from rest_framework import serializers
from .models import Interaction

class InteractionSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(
        source="author.username",
        read_only=True,
    )

    class Meta:
        model = Interaction
        fields = ["id", "ticket", "author", "author_username", "message", "created_at"]
        read_only_fields = ["id", "created_at", "ticket", "author"]