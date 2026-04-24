from rest_framework import serializers


class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True, min_length=6)
    verification_method = serializers.ChoiceField(
        choices=["link", "otp"],
        required=False,
        default="link",
    )


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()  # can be name OR email
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField()
    phone_number = serializers.CharField()


class TokenResponseSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    token_type = serializers.CharField()
    expires_in = serializers.IntegerField()
    user_id = serializers.IntegerField()


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()
