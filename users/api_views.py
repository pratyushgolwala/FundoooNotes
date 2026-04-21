from django.db import IntegrityError
from django.contrib.auth.hashers import make_password, check_password

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema

from users.tasks import send_verification_email

from .models import User
from .serializers import SignupSerializer, LoginSerializer, UserSerializer, TokenResponseSerializer, RefreshTokenSerializer
from .token_utils import generate_tokens, decode_token

from typing import Any, Dict, cast
import jwt


class SignupAPI(APIView):
    @extend_schema(request=SignupSerializer, responses={201: UserSerializer})
    def post(self, request):
        ser = SignupSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        data = cast(Dict[str, Any], ser.validated_data)
        try:
            user = User.objects.create(
                name=data["username"],
                email=data["email"],
                phone_number=data["phone_number"],
                password=make_password(data["password"]),
            )
        except IntegrityError:
            return Response({"detail": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)

        # Send verification email asynchronously
        send_verification_email.delay(user.pk)

        return Response(
            {
                "token_type": "Bearer",
                "expires_in": 3600,
                "user_id": user.pk,
                "user": UserSerializer(user).data  # ✅ Proper structure, no unpacking
            },
            status=status.HTTP_201_CREATED,
        )

class LoginAPI(APIView):
    @extend_schema(request=LoginSerializer, responses={200: TokenResponseSerializer})
    def post(self, request):
        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = cast(Dict[str, Any], ser.validated_data)

        identifier = data["username"]
        password = data["password"]

        user = User.objects.filter(name=identifier).first() or User.objects.filter(email=identifier).first()
        if not user or not check_password(password, user.password):
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        # ✅ CHECK EMAIL VERIFICATION
        if not user.is_email_verified:
            return Response(
                {"detail": "Please verify your email before logging in. Check your inbox for verification link."},
                status=status.HTTP_403_FORBIDDEN
            )

        request.session["user_id"] = user.pk
        tokens = generate_tokens(user.pk)
        tokens["user_id"] = user.pk
        
        return Response(tokens, status=status.HTTP_200_OK)


class HomeAPI(APIView):
    @extend_schema(responses={200: UserSerializer})
    def get(self, request):
        user_id = request.session.get("user_id")
        if not user_id:
            return Response({"detail": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

        user = User.objects.filter(pk=user_id).first()
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


class RefreshTokenAPI(APIView):
    @extend_schema(request=RefreshTokenSerializer, responses={200: TokenResponseSerializer})
    def post(self, request):
        ser = RefreshTokenSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = cast(Dict[str, Any], ser.validated_data)  # type: ignore
        
        refresh_token = data["refresh_token"]
        
        try:
            payload = decode_token(refresh_token)
        except jwt.ExpiredSignatureError:
            return Response({"detail": "Refresh token expired"}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError:
            return Response({"detail": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Verify token is a refresh token
        if payload.get("token_type") != "refresh":
            return Response({"detail": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED)
        
        user_id = payload.get("user_id")
        user = User.objects.filter(pk=user_id).first()
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Generate new tokens
        tokens = generate_tokens(user.pk)
        tokens["user_id"] = user.pk
        
        return Response(tokens, status=status.HTTP_200_OK)
