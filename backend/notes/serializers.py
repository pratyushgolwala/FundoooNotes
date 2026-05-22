from rest_framework import serializers
from .models import Note
from .models import NoteCollaborator
from .models import NoteCollaboratorInvite
from labels.models import Label
from users.models import User


class CollaboratorSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="user.pk")
    name = serializers.CharField(source="user.name")
    email = serializers.EmailField(source="user.email")
    access_level = serializers.CharField()


class CollaboratorAddSerializer(serializers.Serializer):
    email = serializers.EmailField()
    access_level = serializers.ChoiceField(
        choices=[NoteCollaborator.ACCESS_VIEW, NoteCollaborator.ACCESS_EDIT],
        required=False,
        default=NoteCollaborator.ACCESS_VIEW,
    )


class CollaboratorInviteActionSerializer(serializers.Serializer):
    token = serializers.CharField()


class NoteSerializer(serializers.ModelSerializer):
    label_ids = serializers.PrimaryKeyRelatedField(
        source="labels",
        many=True,
        queryset=Label.objects.all(),
        required=False,
    )
    label_names = serializers.SerializerMethodField(read_only=True)
    collaborators = serializers.SerializerMethodField(read_only=True)
    owner = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Note
        fields = [
            "id",
            "owner",
            "label_ids",
            "title",
            "content",
            "label_names",
            "collaborators",
            "created_at",
            "updated_at",
            "is_archived",
            "is_deleted",
            "deleted_at",
            "is_pinned",
            "color",
        ]

    def get_label_names(self, obj):
        return list(obj.labels.values_list("name", flat=True))

    def get_collaborators(self, obj):
        collaborations = NoteCollaborator.objects.filter(note=obj).select_related("user").all()
        return CollaboratorSerializer(collaborations, many=True).data

    def get_owner(self, obj):
        return {
            "name": obj.user.name,
            "email": obj.user.email,
        }


class PendingInvitationSerializer(serializers.ModelSerializer):
    """Serializer for displaying pending invitations to the invited user."""
    note_id = serializers.IntegerField(source="note.id")
    note_title = serializers.CharField(source="note.title")
    invited_by_name = serializers.CharField(source="invited_by.name")
    invited_by_email = serializers.CharField(source="invited_by.email")
    invite_id = serializers.IntegerField(source="id")
    
    class Meta:
        model = NoteCollaboratorInvite
        fields = [
            "invite_id",
            "note_id",
            "note_title",
            "invited_by_name",
            "invited_by_email",
            "access_level",
            "created_at",
        ]