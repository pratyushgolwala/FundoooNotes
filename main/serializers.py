from rest_framework import serializers

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