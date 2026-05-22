"""Collaborators router for FastAPI - handles all collaborator-related endpoints."""
import token

from fastapi import APIRouter, HTTPException, status, Depends, Header
from fastapi.security import HTTPBearer
from typing import List, Optional
from django.core.cache import cache
from django.utils import timezone
from secrets import token_urlsafe

from notes.models import Note, NoteCollaborator, NoteCollaboratorInvite
from users.models import User
from users.tasks import send_note_collaborator_added_email

from ..schemas.collaborators import (
    CollaboratorSchema,
    CollaboratorAddSchema,
    CollaboratorResponseSchema,
    PendingInvitationSchema,
    InvitationActionSchema,
    InvitationResponseSchema,
)
from ..schemas.common import ApiResponseSchema
from common.api_response import build_api_response
from ..utils.auth import verify_auth_header

router = APIRouter(prefix="/fastapi", tags=["collaborators"])
security = HTTPBearer()


def _clear_note_related_caches(note: Note):
    """Clear all caches related to a note."""
    cache_key = f"note_{note.id}"  # type: ignore[attr-defined]
    cache.delete(cache_key)
    # Also clear user notes cache
    cache_key = f"user_notes_{note.user.id}"  # type: ignore[attr-defined]
    cache.delete(cache_key)


def _get_owned_note(note_id: int, user: User) -> Optional[Note]:
    """Get a note if the user is the owner."""
    return Note.objects.filter(id=note_id, user=user).first()


def _verify_credentials(credentials = Depends(security)) -> str:
    """Extract and verify bearer token from credentials."""
    return f"Bearer {credentials.credentials}"


@router.get("/notes/{note_id}/collaborators/", response_model=ApiResponseSchema)
def list_collaborators(note_id: int, token: str = Depends(_verify_credentials)):
    """Get all collaborators for a note (owner only)."""
    user = verify_auth_header(token)
    
    note = _get_owned_note(note_id, user)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    collaborations = NoteCollaborator.objects.filter(
        note=note
    ).select_related("user").order_by("user__name")
    
    payload = [
        CollaboratorSchema(
            name=collab.user.name,
            access_level=collab.access_level,
        )
        for collab in collaborations
    ]
    return build_api_response("Collaborators fetched", [item.dict() for item in payload], status.HTTP_200_OK)


@router.post("/notes/{note_id}/collaborators/", response_model=ApiResponseSchema, status_code=status.HTTP_201_CREATED)
def add_collaborator(note_id: int, data: CollaboratorAddSchema, token: str = Depends(_verify_credentials)):
    """Add a collaborator to a note (owner only)."""
    user = verify_auth_header(token)
    
    note = _get_owned_note(note_id, user)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    email = data.email
    access_level = data.access_level or "view"
    
    collaborator = User.objects.filter(email=email).first()
    if not collaborator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if collaborator.pk == user.pk:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner is already part of the note"
        )
    
    collaboration = NoteCollaborator.objects.filter(
        note=note, user=collaborator
    ).select_related("user").first()
    if collaboration:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a collaborator"
        )
    
    invite = NoteCollaboratorInvite.objects.filter(
        note=note, invited_user=collaborator
    ).first()
    
    if invite and invite.status == NoteCollaboratorInvite.STATUS_PENDING:
        invite.access_level = access_level
        invite.invited_by = user
        invite.save(update_fields=["access_level", "invited_by", "token"])
    else:
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
    
    payload = CollaboratorResponseSchema(
        name=collaborator.name,
        status=NoteCollaboratorInvite.STATUS_PENDING,
    )
    return build_api_response("Collaborator added", payload.dict(), status.HTTP_201_CREATED)


@router.patch("/notes/{note_id}/collaborators/{user_id}/", response_model=ApiResponseSchema)
def update_collaborator(note_id: int, user_id: int, data: CollaboratorAddSchema, token: str = Depends(_verify_credentials)):
    """Update collaborator access level (owner only)."""
    user = verify_auth_header(token)
    
    note = _get_owned_note(note_id, user)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    collaboration = NoteCollaborator.objects.filter(
        note=note, user_id=user_id
    ).select_related("user").first()
    if not collaboration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collaborator not found"
        )
    
    collaboration.access_level = data.access_level or collaboration.access_level
    collaboration.save(update_fields=["access_level"])
    
    _clear_note_related_caches(note)
    
    payload = CollaboratorSchema(
        name=collaboration.user.name,
        access_level=collaboration.access_level,
    )
    return build_api_response("Collaborator updated", payload.dict(), status.HTTP_200_OK)


@router.delete("/notes/{note_id}/collaborators/{user_id}/", status_code=status.HTTP_204_NO_CONTENT)
def remove_collaborator(note_id: int, user_id: int, token: str = Depends(_verify_credentials)):
    """Remove a collaborator from a note (owner only)."""
    user = verify_auth_header(token)
    
    note = _get_owned_note(note_id, user)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    collaboration = NoteCollaborator.objects.filter(
        note=note, user_id=user_id
    ).select_related("user").first()
    if not collaboration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collaborator not found"
        )
    
    collaboration.delete()
    _clear_note_related_caches(note)
    
    return None


@router.get("/invitations/", response_model=ApiResponseSchema)
def list_pending_invitations(token: str = Depends(_verify_credentials)):
    """Get all pending invitations for the current user."""
    user = verify_auth_header(token)
    
    pending_invites = NoteCollaboratorInvite.objects.filter(
        invited_user=user,
        status=NoteCollaboratorInvite.STATUS_PENDING,
    ).select_related("note", "invited_by").order_by("-created_at")
    
    payload = [
        PendingInvitationSchema(
            invited_by=invite.invited_by.name,
        )
        for invite in pending_invites
    ]
    return build_api_response("Pending invitations fetched", [item.dict() for item in payload], status.HTTP_200_OK)


@router.post("/invitations/", response_model=ApiResponseSchema)
def respond_to_invitation(data: InvitationActionSchema, token: str = Depends(_verify_credentials)):
    """Accept or decline a pending invitation."""
    user = verify_auth_header(token)
    
    invite_id = data.invite_id
    action = data.action
    
    if action not in ["accept", "decline"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request. Action must be 'accept' or 'decline'."
        )
    
    try:
        invite = NoteCollaboratorInvite.objects.select_related("note").filter(
            id=invite_id,
            invited_user=user,
            status=NoteCollaboratorInvite.STATUS_PENDING,
        ).first()
        
        if not invite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found or already handled."
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
            payload = InvitationResponseSchema(detail="Invitation accepted")
            return build_api_response("Invitation accepted", payload.dict(), status.HTTP_200_OK)
        
        if action == "decline":
            invite.status = NoteCollaboratorInvite.STATUS_DECLINED
            invite.responded_at = timezone.now()
            invite.save(update_fields=["status", "responded_at"])
            _clear_note_related_caches(invite.note)
            payload = InvitationResponseSchema(detail="Invitation declined")
            return build_api_response("Invitation declined", payload.dict(), status.HTTP_200_OK)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing invitation: {str(e)}"
        )