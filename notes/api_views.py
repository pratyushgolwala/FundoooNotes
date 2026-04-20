import jwt
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, cast

from django.conf import settings
from django.contrib.auth.hashers import check_password

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema

from users.models import User
from users.serializers import LoginSerializer
from .models import Note
from .serializers import NoteSerializer


def _get_bearer_token(request):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip()


def _decode_token(token):
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])


def _get_user_from_request(request):
    token = _get_bearer_token(request)
    if not token:
        return None, Response({"detail": "Missing Bearer token"}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        payload = _decode_token(token)
    except jwt.ExpiredSignatureError:
        return None, Response({"detail": "Token expired"}, status=status.HTTP_401_UNAUTHORIZED)
    except jwt.InvalidTokenError:
        return None, Response({"detail": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    user_id = payload.get("user_id")
    user = User.objects.filter(pk=user_id).first()
    if not user:
        return None, Response({"detail": "User not found"}, status=status.HTTP_401_UNAUTHORIZED)
    return user, None


class TokenAPI(APIView):
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

        payload = {
            "user_id": user.pk,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        return Response({"token": token, "user_id": user.pk}, status=status.HTTP_200_OK)


class NotesAPI(APIView):
    @extend_schema(responses={200: NoteSerializer(many=True)})
    def get(self, request):
        user, error = _get_user_from_request(request)
        if error:
            return error

        label_id = request.query_params.get("label")
        notes = Note.objects.filter(user=user).order_by("-created_at")
        if label_id:
            notes = notes.filter(label_id=label_id)
        return Response(NoteSerializer(notes, many=True).data, status=status.HTTP_200_OK)

    @extend_schema(request=NoteSerializer, responses={201: NoteSerializer})
    def post(self, request):
        user, error = _get_user_from_request(request)
        if error:
            return error

        ser = NoteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        note = ser.save(user=user)
        return Response(NoteSerializer(note).data, status=status.HTTP_201_CREATED)


class NoteDetailAPI(APIView):
    @extend_schema(responses={200: NoteSerializer})
    def get(self, request, note_id):
        user, error = _get_user_from_request(request)
        if error:
            return error

        note = Note.objects.filter(pk=note_id, user=user).first()
        if not note:
            return Response({"detail": "Note not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(NoteSerializer(note).data, status=status.HTTP_200_OK)

    @extend_schema(request=NoteSerializer, responses={200: NoteSerializer})
    def put(self, request, note_id):
        user, error = _get_user_from_request(request)
        if error:
            return error

        note = Note.objects.filter(pk=note_id, user=user).first()
        if not note:
            return Response({"detail": "Note not found"}, status=status.HTTP_404_NOT_FOUND)
        ser = NoteSerializer(note, data=request.data, partial=False)
        ser.is_valid(raise_exception=True)
        note = ser.save(user=user)
        return Response(NoteSerializer(note).data, status=status.HTTP_200_OK)

    def delete(self, request, note_id):
        user, error = _get_user_from_request(request)
        if error:
            return error

        note = Note.objects.filter(pk=note_id, user=user).first()
        if not note:
            return Response({"detail": "Note not found"}, status=status.HTTP_404_NOT_FOUND)
        note.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
