from rest_framework import serializers

from .models import Label, Note

class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True, min_length=6)

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()  # can be name OR email
    password = serializers.CharField(write_only=True)

class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField()
    phone_number = serializers.CharField()


class NoteSerializer(serializers.ModelSerializer):
    label_id = serializers.PrimaryKeyRelatedField(
        source="label",
        queryset=Label.objects.all(),
        allow_null=True,
        required=False,
    )
    label_name = serializers.CharField(source="label.name", read_only=True)

    class Meta:
        model = Note
        fields = ["id", "title", "content", "label_id", "label_name", "created_at"]