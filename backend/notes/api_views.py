import jwt
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone
from typing import Any, Dict, cast

from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import UserRateThrottle

from drf_spectacular.utils import extend_schema

from common.api_response import EnvelopeAPIView
from users.models import User
from users.serializers import LoginSerializer, TokenResponseSerializer
from users.token_utils import generate_tokens, decode_token
from users.tasks import send_verification_email, send_note_collaborator_added_email

from .models import Note
from .models import NoteCollaborator
from .models import NoteCollaboratorInvite
from .serializers import NoteSerializer, CollaboratorAddSerializer, CollaboratorSerializer, PendingInvitationSerializer


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

    if payload.get("token_type") != "access":
        return None, Response({"detail": "Invalid token type"}, status=status.HTTP_401_UNAUTHORIZED)

    user_id = payload.get("user_id")
    user = User.objects.filter(pk=user_id).first()
    if not user:
        return None, Response({"detail": "User not found"}, status=status.HTTP_401_UNAUTHORIZED)

    return user, None


def _is_note_owner(note, user):
    return note.user_id == user.id


def _can_access_note(note, user):
    return (
        note.user_id == user.id
        or NoteCollaborator.objects.filter(note=note, user_id=user.id).exists()
        or NoteCollaboratorInvite.objects.filter(note=note, invited_user=user, status=NoteCollaboratorInvite.STATUS_PENDING).exists()
    )


def _get_note_access_level(note, user):
    if note.user_id == user.id:
        return "owner"

    pending_invite = NoteCollaboratorInvite.objects.filter(
        note=note,
        invited_user=user,
        status=NoteCollaboratorInvite.STATUS_PENDING,
    ).first()
    if pending_invite:
        return "pending"

    collaboration = NoteCollaborator.objects.filter(note=note, user_id=user.id).first()
    if collaboration:
        return collaboration.access_level

    return None


def _can_edit_note(note, user):
    access_level = _get_note_access_level(note, user)
    return access_level in {"owner", "edit"}


def _get_accessible_note(note_id, user, include_deleted=False):
    filters = Q(user=user) | Q(collaborators=user) | Q(collaborator_invites__invited_user=user, collaborator_invites__status=NoteCollaboratorInvite.STATUS_PENDING)
    if include_deleted:
        return (
            Note.objects
            .prefetch_related("labels", "collaborators", "notecollaborator_set__user", "collaborator_invites__invited_user")
            .filter(pk=note_id)
            .filter(filters)
            .distinct()
            .first()
        )

    return (
        Note.objects
        .prefetch_related("labels", "collaborators", "notecollaborator_set__user", "collaborator_invites__invited_user")
        .filter(pk=note_id)
        .filter(filters, is_deleted=False)
        .distinct()
        .first()
    )


def _get_owned_note(note_id, user, include_deleted=False):
    filters = {"pk": note_id, "user": user}
    if not include_deleted:
        filters["is_deleted"] = False

    return (
        Note.objects
        .prefetch_related("labels", "collaborators", "notecollaborator_set__user", "collaborator_invites__invited_user")
        .filter(**filters)
        .first()
    )


def _get_user_notes_cache_key(user_id, label_id=None):
    if label_id:
        return f"user_notes:{user_id}:label:{label_id}"
    return f"user_notes:{user_id}"


def _get_note_cache_key(note_id):
    return f"note:{note_id}"


def _clear_user_notes_cache(user_id):
    cache.delete(f"user_notes:{user_id}")
    for i in range(1, 100):
        cache.delete(f"user_notes:{user_id}:label:{i}")


def _clear_note_related_caches(note):
    user_ids = {note.user_id}
    user_ids.update(NoteCollaborator.objects.filter(note=note).values_list("user_id", flat=True))
    user_ids.update(NoteCollaboratorInvite.objects.filter(note=note).values_list("invited_user_id", flat=True))

    cache.delete(_get_note_cache_key(note.id))
    for user_id in user_ids:
        _clear_user_notes_cache(user_id)


class TokenAPI(EnvelopeAPIView):
    throttle_classes = [TokenRateThrottle]
    response_messages = {
        "POST": "Login successful",
    }

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

        tokens = generate_tokens(user.pk)
        tokens["user_id"] = user.pk
        return Response(tokens, status=status.HTTP_200_OK)


class NotesAPI(EnvelopeAPIView):
    throttle_classes = [NotesRateThrottle]
    response_messages = {
        "GET": "Notes fetched",
        "POST": "Note created",
    }

    @extend_schema(responses={200: NoteSerializer(many=True)})
    def get(self, request):
        user, error = _get_user_from_request(request)
        if error:
            return error
        assert user is not None

        cache_key = _get_user_notes_cache_key(user.pk)
        cached_notes = cache.get(cache_key)
        if cached_notes is not None:
            return Response(cached_notes, status=status.HTTP_200_OK)

        notes = (
            Note.objects
            .filter(
                Q(user=user)
                | Q(notecollaborator__user=user)
                | Q(collaborator_invites__invited_user=user, collaborator_invites__status=NoteCollaboratorInvite.STATUS_PENDING)
            )
            .distinct()
            .order_by("-created_at")
            .prefetch_related("labels", "collaborators", "notecollaborator_set__user", "collaborator_invites__invited_user")
        )

        serialized_notes = NoteSerializer(notes, many=True, context={"request_user": user}).data
        cache.set(cache_key, serialized_notes, timeout=300)
        return Response(serialized_notes, status=status.HTTP_200_OK)

    @extend_schema(request=NoteSerializer, responses={201: NoteSerializer})
    def post(self, request):
        user, error = _get_user_from_request(request)
        if error:
            return error
        assert user is not None

        ser = NoteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        note = ser.save(user=user)

        _clear_user_notes_cache(user.pk)
        return Response(NoteSerializer(note, context={"request_user": user}).data, status=status.HTTP_201_CREATED)


class NoteDetailAPI(EnvelopeAPIView):
    throttle_classes = [NotesRateThrottle]
    response_messages = {
        "GET": "Note fetched",
        "PUT": "Note updated",
        "PATCH": "Note updated",
    }

    @extend_schema(responses={200: NoteSerializer})
    def get(self, request, note_id):
        user, error = _get_user_from_request(request)
        if error:
            return error
        assert user is not None

        cache_key = _get_note_cache_key(note_id)
        cached_note = cache.get(cache_key)
        if cached_note is not None:
            return Response(cached_note, status=status.HTTP_200_OK)

        note = _get_accessible_note(note_id, user)
        if not note:
            return Response({"detail": "Note not found"}, status=status.HTTP_404_NOT_FOUND)

        serialized_note = NoteSerializer(note, context={"request_user": user}).data
        cache.set(cache_key, serialized_note)
        return Response(serialized_note, status=status.HTTP_200_OK)

    @extend_schema(request=NoteSerializer, responses={200: NoteSerializer})
    def put(self, request, note_id):
        user, error = _get_user_from_request(request)
        if error:
            return error
        assert user is not None

        note = _get_accessible_note(note_id, user)
        if not note:
            return Response({"detail": "Note not found"}, status=status.HTTP_404_NOT_FOUND)

        if not _can_edit_note(note, user):
            return Response({"detail": "You do not have edit access"}, status=status.HTTP_403_FORBIDDEN)

        ser = NoteSerializer(note, data=request.data, partial=False)
        ser.is_valid(raise_exception=True)
        note = ser.save(user=note.user)

        _clear_note_related_caches(note)
        return Response(NoteSerializer(note, context={"request_user": user}).data, status=status.HTTP_200_OK)

    @extend_schema(request=NoteSerializer, responses={200: NoteSerializer})
    def patch(self, request, note_id):
        user, error = _get_user_from_request(request)
        if error:
            return error
        assert user is not None

        note = _get_accessible_note(note_id, user)
        if not note:
            return Response({"detail": "Note not found"}, status=status.HTTP_404_NOT_FOUND)

        if not _can_edit_note(note, user):
            return Response({"detail": "You do not have edit access"}, status=status.HTTP_403_FORBIDDEN)

        ser = NoteSerializer(note, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        note = ser.save(user=note.user)

        _clear_note_related_caches(note)
        return Response(NoteSerializer(note, context={"request_user": user}).data, status=status.HTTP_200_OK)

    @extend_schema(responses={204: None})
    def delete(self, request, note_id):
        user, error = _get_user_from_request(request)
        if error:
            return error
        assert user is not None

        note = _get_owned_note(note_id, user)
        if not note:
            return Response({"detail": "Note not found"}, status=status.HTTP_404_NOT_FOUND)

        note.is_deleted = True
        note.deleted_at = timezone.now()
        note.is_archived = False
        note.save(update_fields=["is_deleted", "deleted_at", "is_archived", "updated_at"])
        _clear_note_related_caches(note)
        return Response(status=status.HTTP_204_NO_CONTENT)


class NoteRestoreAPI(EnvelopeAPIView):
    throttle_classes = [NotesRateThrottle]
    response_messages = {
        "POST": "Note restored",
    }

    @extend_schema(responses={200: NoteSerializer})
    def post(self, request, note_id):
        user, error = _get_user_from_request(request)
        if error:
            return error
        assert user is not None

        note = _get_owned_note(note_id, user, include_deleted=True)
        if not note or not note.is_deleted:
            return Response({"detail": "Note not found"}, status=status.HTTP_404_NOT_FOUND)

        note.is_deleted = False
        note.deleted_at = None
        note.save(update_fields=["is_deleted", "deleted_at", "updated_at"])

        _clear_note_related_caches(note)
        return Response(NoteSerializer(note, context={"request_user": user}).data, status=status.HTTP_200_OK)


class NotePermanentDeleteAPI(EnvelopeAPIView):
    throttle_classes = [NotesRateThrottle]
    response_messages = {
        "DELETE": "Note permanently deleted",
    }

    @extend_schema(responses={204: None})
    def delete(self, request, note_id):
        user, error = _get_user_from_request(request)
        if error:
            return error
        assert user is not None

        note = _get_owned_note(note_id, user, include_deleted=True)
        if not note or not note.is_deleted:
            return Response({"detail": "Note not found"}, status=status.HTTP_404_NOT_FOUND)

        _clear_note_related_caches(note)
        note.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NoteCollaboratorsAPI(EnvelopeAPIView):
    throttle_classes = [NotesRateThrottle]
    response_messages = {
        "GET": "Collaborators fetched",
        "POST": "Collaborator added",
    }

    @extend_schema(responses={200: CollaboratorSerializer(many=True)})
    def get(self, request, note_id):
        user, error = _get_user_from_request(request)
        if error:
            return error
        assert user is not None

        note = _get_owned_note(note_id, user)
        if not note:
            return Response({"detail": "Note not found"}, status=status.HTTP_404_NOT_FOUND)

        collaborations = NoteCollaborator.objects.filter(note=note).select_related("user").order_by("user__name")
        return Response(CollaboratorSerializer(collaborations, many=True).data, status=status.HTTP_200_OK)

    @extend_schema(request=CollaboratorAddSerializer, responses={201: CollaboratorSerializer})
    def post(self, request, note_id):
        user, error = _get_user_from_request(request)
        if error:
            return error
        assert user is not None

        note = _get_owned_note(note_id, user)
        if not note:
            return Response({"detail": "Note not found"}, status=status.HTTP_404_NOT_FOUND)

        ser = CollaboratorAddSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = cast(Dict[str, Any], ser.validated_data)
        email = data["email"]
        access_level = data.get("access_level", "view")

        collaborator = User.objects.filter(email=email).first()
        if not collaborator:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        if collaborator.pk == user.pk:
            return Response({"detail": "Owner is already part of the note"}, status=status.HTTP_400_BAD_REQUEST)

        collaboration = NoteCollaborator.objects.filter(note=note, user=collaborator).select_related("user").first()
        if collaboration:
            return Response({"detail": "User is already a collaborator"}, status=status.HTTP_400_BAD_REQUEST)

        invite = NoteCollaboratorInvite.objects.filter(note=note, invited_user=collaborator).first()
        if invite and invite.status == NoteCollaboratorInvite.STATUS_PENDING:
            invite.access_level = access_level
            invite.invited_by = user
            invite.save(update_fields=["access_level", "invited_by", "token", "status", "updated_at"])
        else:
            from secrets import token_urlsafe
            invite = NoteCollaboratorInvite.objects.create(
                note=note,
                invited_user=collaborator,
                invited_by=user,
                access_level=access_level,
                token=token_urlsafe(24),
                status=NoteCollaboratorInvite.STATUS_PENDING,
            )

        send_note_collaborator_added_email.delay(invite.pk)

        _clear_note_related_caches(note)
        return Response(
            {
                "id": collaborator.pk,
                "name": collaborator.name,
                "email": collaborator.email,
                "access_level": access_level,
                "status": NoteCollaboratorInvite.STATUS_PENDING,
                "token": invite.token,
            },
            status=status.HTTP_201_CREATED,
        )


class NoteCollaboratorDetailAPI(EnvelopeAPIView):
    throttle_classes = [NotesRateThrottle]
    response_messages = {
        "PATCH": "Collaborator updated",
        "DELETE": "Collaborator removed",
    }

    @extend_schema(request=CollaboratorAddSerializer, responses={200: CollaboratorSerializer})
    def patch(self, request, note_id, user_id):
        user, error = _get_user_from_request(request)
        if error:
            return error
        assert user is not None

        note = _get_owned_note(note_id, user)
        if not note:
            return Response({"detail": "Note not found"}, status=status.HTTP_404_NOT_FOUND)

        collaboration = NoteCollaborator.objects.filter(note=note, user_id=user_id).select_related("user").first()
        if not collaboration:
            return Response({"detail": "Collaborator not found"}, status=status.HTTP_404_NOT_FOUND)

        ser = CollaboratorAddSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = cast(Dict[str, Any], ser.validated_data)
        collaboration.access_level = data.get("access_level", collaboration.access_level)
        collaboration.save(update_fields=["access_level", "updated_at"])

        _clear_note_related_caches(note)
        return Response(CollaboratorSerializer(collaboration).data, status=status.HTTP_200_OK)

    @extend_schema(responses={204: None})
    def delete(self, request, note_id, user_id):
        user, error = _get_user_from_request(request)
        if error:
            return error
        assert user is not None

        note = _get_owned_note(note_id, user)
        if not note:
            return Response({"detail": "Note not found"}, status=status.HTTP_404_NOT_FOUND)

        collaboration = NoteCollaborator.objects.filter(note=note, user_id=user_id).select_related("user").first()
        if not collaboration:
            return Response({"detail": "Collaborator not found"}, status=status.HTTP_404_NOT_FOUND)

        collaboration.delete()
        _clear_note_related_caches(note)
        return Response(status=status.HTTP_204_NO_CONTENT)


class NoteInvitationActionAPI(EnvelopeAPIView):
    throttle_classes = [NotesRateThrottle]
    response_messages = {
        "POST": "Invitation processed",
        "GET": "Invitation processed",
    }

    @extend_schema(responses={200: None})
    def post(self, request, token, action):
        return self._handle_invitation_action(token, action)

    @extend_schema(responses={200: None})
    def get(self, request, token, action):
        return self._handle_invitation_action(token, action)

    def _handle_invitation_action(self, token, action):
        invite = NoteCollaboratorInvite.objects.select_related("note", "invited_user", "invited_by").filter(token=token).first()
        if not invite:
            return Response({"detail": "Invitation not found"}, status=status.HTTP_404_NOT_FOUND)

        if invite.status != NoteCollaboratorInvite.STATUS_PENDING:
            return Response({"detail": "Invitation already handled"}, status=status.HTTP_400_BAD_REQUEST)

        if action == "accept":
            NoteCollaborator.objects.update_or_create(
                note=invite.note,
                user=invite.invited_user,
                defaults={"access_level": invite.access_level},
            )
            invite.status = NoteCollaboratorInvite.STATUS_ACCEPTED
            invite.responded_at = timezone.now()
            invite.save(update_fields=["status", "responded_at"])
            _clear_note_related_caches(invite.note)
            return Response({"detail": "Invitation accepted"}, status=status.HTTP_200_OK)

        if action == "decline":
            invite.status = NoteCollaboratorInvite.STATUS_DECLINED
            invite.responded_at = timezone.now()
            invite.save(update_fields=["status", "responded_at"])
            _clear_note_related_caches(invite.note)
            return Response({"detail": "Invitation declined"}, status=status.HTTP_200_OK)

        return Response({"detail": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)


class PendingInvitationsAPI(EnvelopeAPIView):
    """API endpoint to list and respond to pending invitations."""
    throttle_classes = [NotesRateThrottle]
    response_messages = {
        "GET": "Pending invitations fetched",
        "POST": "Invitation response recorded",
    }

    @extend_schema(
        summary="Get pending invitations for the current user",
        responses={200: PendingInvitationSerializer(many=True)},
    )
    def get(self, request):
        """Fetch all pending invitations for the authenticated user."""
        user, error_response = _get_user_from_request(request)
        if error_response:
            return error_response

        pending_invites = NoteCollaboratorInvite.objects.filter(
            invited_user=user,
            status=NoteCollaboratorInvite.STATUS_PENDING,
        ).select_related("note", "invited_by").order_by("-created_at")

        serializer = PendingInvitationSerializer(pending_invites, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Respond to an invitation (accept or decline)",
        request={
            "type": "object",
            "properties": {
                "invite_id": {"type": "integer"},
                "action": {"type": "string", "enum": ["accept", "decline"]},
            },
            "required": ["invite_id", "action"],
        },
        responses={200: {"type": "object"}, 400: {"type": "object"}},
    )
    def post(self, request):
        """Accept or decline a pending invitation."""
        user, error_response = _get_user_from_request(request)
        if error_response:
            return error_response

        invite_id = request.data.get("invite_id")
        action = request.data.get("action")

        if not invite_id or action not in ["accept", "decline"]:
            return Response(
                {"detail": "Invalid request. Provide invite_id and action (accept/decline)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            invite = NoteCollaboratorInvite.objects.select_related("note").filter(
                id=invite_id,
                invited_user=user,
                status=NoteCollaboratorInvite.STATUS_PENDING,
            ).first()

            if not invite:
                return Response(
                    {"detail": "Invitation not found or already handled."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if action == "accept":
                NoteCollaborator.objects.update_or_create(
                    note=invite.note,
                    user=user,
                    defaults={"access_level": invite.access_level},
                )
                invite.status = NoteCollaboratorInvite.STATUS_ACCEPTED
                invite.responded_at = timezone.now()
                invite.save(update_fields=["status", "responded_at"])
                _clear_note_related_caches(invite.note)
                return Response({"detail": "Invitation accepted"}, status=status.HTTP_200_OK)

            if action == "decline":
                invite.status = NoteCollaboratorInvite.STATUS_DECLINED
                invite.responded_at = timezone.now()
                invite.save(update_fields=["status", "responded_at"])
                _clear_note_related_caches(invite.note)
                return Response({"detail": "Invitation declined"}, status=status.HTTP_200_OK)

            return Response({"detail": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {"detail": f"Error processing invitation: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )