from django.db import models
from users.models import User
from labels.models import Label


class NoteCollaborator(models.Model):
    ACCESS_VIEW = "view"
    ACCESS_EDIT = "edit"

    ACCESS_LEVEL_CHOICES = [
        (ACCESS_VIEW, "Can view"),
        (ACCESS_EDIT, "Can edit"),
    ]

    note = models.ForeignKey("Note", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    access_level = models.CharField(max_length=10, choices=ACCESS_LEVEL_CHOICES, default=ACCESS_VIEW)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("note", "user")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user.email} -> {self.note.id} ({self.access_level})"


class NoteCollaboratorInvite(models.Model):
    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_DECLINED = "declined"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_DECLINED, "Declined"),
    ]

    note = models.ForeignKey("Note", on_delete=models.CASCADE, related_name="collaborator_invites")
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="note_collaborator_invites")
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_note_collaborator_invites")
    access_level = models.CharField(max_length=10, choices=NoteCollaborator.ACCESS_LEVEL_CHOICES, default=NoteCollaborator.ACCESS_VIEW)
    token = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("note", "invited_user")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.invited_user.email} -> {self.note.id} ({self.status})"


class Note(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    collaborators = models.ManyToManyField(
        User,
        blank=True,
        related_name="shared_notes",
        through="NoteCollaborator",
    )
    title = models.CharField(max_length=200)
    labels = models.ManyToManyField(Label, blank=True, related_name="notes")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_pinned = models.BooleanField(default=False)
    color = models.CharField(max_length=7, default="#FFFFFF")

    class Meta:
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self):
        return self.title