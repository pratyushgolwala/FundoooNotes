from django.db import IntegrityError
from django.contrib.auth.hashers import make_password, check_password

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema

from .models import User
from .serializers import SignupSerializer, LoginSerializer, UserSerializer

from typing import Any, Dict, cast


class SignupAPI(APIView):
    @extend_schema(request=SignupSerializer, responses={201: UserSerializer})
    def post(self, request):
        ser = SignupSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        data = cast(Dict[str, Any], ser.validated_data)  # type: ignore
        try:
            user = User.objects.create(
                name=data["username"],
                email=data["email"],
                phone_number=data["phone_number"],
                password=make_password(data["password"]),
            )
        except IntegrityError:
            return Response({"detail": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class LoginAPI(APIView):
    @extend_schema(request=LoginSerializer, responses={200: dict})
    def post(self, request):
        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = cast(Dict[str, Any], ser.validated_data)  # type: ignore

        identifier = data["username"]
        password = data["password"]

        user = User.objects.filter(name=identifier).first() or User.objects.filter(email=identifier).first()
        if not user or not check_password(password, user.password):
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        request.session["user_id"] = user.pk
        return Response({"detail": "Logged in", "user_id": user.pk}, status=status.HTTP_200_OK)


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
