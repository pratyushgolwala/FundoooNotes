import jwt
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, cast

from django.conf import settings
from django.db import models
from django.contrib.auth.hashers import check_password
from django.core.cache import cache

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.throttling import UserRateThrottle

from drf_spectacular.utils import extend_schema

from users.models import User
from users.serializers import LoginSerializer, TokenResponseSerializer
from users.token_utils import generate_tokens, decode_token
from .models import Note
from .serializers import NoteSerializer
from users.tasks import send_verification_email


class NotesRateThrottle(UserRateThrottle):
    scope = "notes"


class TokenRateThrottle(UserRateThrottle):
    scope = "user"


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

    # Verify token is an access token (bearer token), not refresh token
    if payload.get("token_type") != "access":
        return None, Response({"detail": "Invalid token type"}, status=status.HTTP_401_UNAUTHORIZED)

    user_id = payload.get("user_id")
    user = User.objects.filter(pk=user_id).first()
    if not user:
        return None, Response({"detail": "User not found"}, status=status.HTTP_401_UNAUTHORIZED)
    return user, None


# Cache helper functions
def _get_user_notes_cache_key(user_id, label_id=None):
    """Generate a cache key for user notes"""
    if label_id:
        return f"user_notes:{user_id}:label:{label_id}"
    return f"user_notes:{user_id}"


def _get_note_cache_key(note_id):
    """Generate a cache key for a single note"""
    return f"note:{note_id}"


def _clear_user_notes_cache(user_id):
    """Clear all note caches for a user"""
    # Clear all possible cache keys for this user
    cache.delete(f"user_notes:{user_id}")
    # Clear all label-filtered caches
    for i in range(1, 100):  # Clear up to 100 label filters
        cache.delete(f"user_notes:{user_id}:label:{i}")


class TokenAPI(APIView):
    throttle_classes = [TokenRateThrottle]

    @extend_schema(request=LoginSerializer, responses={200: TokenResponseSerializer})
    def post(self, request):
        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = cast(Dict[str, Any], ser.validated_data)  # type: ignore

        identifier = data["username"]
        password = data["password"]

        user = User.objects.filter(name=identifier).first() or User.objects.filter(email=identifier).first()
        if not user or not check_password(password, user.password):
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        # Generate both bearer and refresh tokens
        tokens = generate_tokens(user.pk)
        tokens["user_id"] = user.pk

        return Response(tokens, status=status.HTTP_200_OK)

class NotesAPI(APIView):
    throttle_classes = [NotesRateThrottle]

    @extend_schema(responses={200: NoteSerializer(many=True)})
    def get(self, request):
        user, error = _get_user_from_request(request)
        if error:
            return error
        assert user is not None  # Type guard for Pylance

        # Get all notes for user as starting point
        notes = Note.objects.filter(user=user)
        
        # 🔍 Search filter
        search_query = request.query_params.get("search")
        if search_query:
            notes = notes.filter(
                models.Q(title__icontains=search_query) | 
                models.Q(content__icontains=search_query)
            )
        
        # 📌 Pin filter
        pin = request.query_params.get("pin")
        if pin and pin.lower() == "true":
            notes = notes.filter(is_pinned=True)
        
        # 📦 Archive filter
        archive = request.query_params.get("archive")
        if archive and archive.lower() == "true":
            notes = notes.filter(is_archived=True)
        elif not archive:
            # By default, don't show archived notes unless explicitly requested
            notes = notes.filter(is_archived=False)
        
        # 🏷️ Label filter
        label_id = request.query_params.get("label")
        if label_id:
            notes = notes.filter(label_id=label_id)
        
        # 🎨 Color filter
        color = request.query_params.get("color")
        if color:
            notes = notes.filter(color=color)
        
        # 📊 Sorting
        sort_by = request.query_params.get("sort", "-is_pinned,-created_at")
        try:
            notes = notes.order_by(*sort_by.split(","))
        except:
            notes = notes.order_by("-is_pinned", "-created_at")
        
        # ✅ Check cache before pagination
        cache_key = f"user_notes:{user.pk}:q:{search_query}:pin:{pin}:archive:{archive}:label:{label_id}:color:{color}:sort:{sort_by}"
        cached_notes = cache.get(cache_key)
        
        if cached_notes is not None:
            return Response(cached_notes, status=status.HTTP_200_OK)
        
        # 📄 Pagination
        paginator = PageNumberPagination()
        paginator.page_size = 10
        paginated_notes = paginator.paginate_queryset(notes, request)
        serialized_notes = NoteSerializer(paginated_notes, many=True).data
        
        # Add pagination info to response
        response_data = {
            "count": paginator.page.paginator.count,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "results": serialized_notes
        }
        
        # Cache the result
        cache.set(cache_key, response_data, timeout=300)
        
        return Response(response_data, status=status.HTTP_200_OK)

    @extend_schema(request=NoteSerializer, responses={201: NoteSerializer})
    def post(self, request):
        user, error = _get_user_from_request(request)
        if error:
            return error
        assert user is not None  # Type guard for Pylance

        ser = NoteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        note = ser.save(user=user)
        
        # Clear cache when a new note is created
        _clear_user_notes_cache(user.pk)
        
        return Response(NoteSerializer(note).data, status=status.HTTP_201_CREATED)


class NoteDetailAPI(APIView):
    throttle_classes = [NotesRateThrottle]

    @extend_schema(responses={200: NoteSerializer})
    def get(self, request, note_id):
        user, error = _get_user_from_request(request)
        if error:
            return error
        assert user is not None  # Type guard for Pylance

        # Check cache first
        cache_key = _get_note_cache_key(note_id)
        cached_note = cache.get(cache_key)
        
        if cached_note is not None:
            return Response(cached_note, status=status.HTTP_200_OK)

        note = Note.objects.filter(pk=note_id, user=user).first()
        if not note:
            return Response({"detail": "Note not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Cache the note
        serialized_note = NoteSerializer(note).data
        cache.set(cache_key, serialized_note)
        
        return Response(serialized_note, status=status.HTTP_200_OK)

    @extend_schema(request=NoteSerializer, responses={200: NoteSerializer})
    def put(self, request, note_id):
        user, error = _get_user_from_request(request)
        if error:
            return error
        assert user is not None  # Type guard for Pylance

        note = Note.objects.filter(pk=note_id, user=user).first()
        if not note:
            return Response({"detail": "Note not found"}, status=status.HTTP_404_NOT_FOUND)
        ser = NoteSerializer(note, data=request.data, partial=False)
        ser.is_valid(raise_exception=True)
        note = ser.save(user=user)
        
        # Clear cache when note is updated
        _clear_user_notes_cache(user.pk)
        cache.delete(_get_note_cache_key(note_id))
        
        return Response(NoteSerializer(note).data, status=status.HTTP_200_OK)

    @extend_schema(responses={204: None})
    def delete(self, request, note_id):
        user, error = _get_user_from_request(request)
        if error:
            return error
        assert user is not None  # Type guard for Pylance

        note = Note.objects.filter(pk=note_id, user=user).first()
        if not note:
            return Response({"detail": "Note not found"}, status=status.HTTP_404_NOT_FOUND)
        note.delete()
        
        # Clear cache when note is deleted
        _clear_user_notes_cache(user.pk)
        cache.delete(_get_note_cache_key(note_id))
        
        return Response(status=status.HTTP_204_NO_CONTENT)