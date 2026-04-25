import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from notes.models import Note
from labels.models import Label
from users.models import User

@pytest.mark.django_db
class TestNoteModel:
    def test_create_note(self):
        user = User.objects.create(
            name="Note User",
            email="noteuser@example.com",
            phone_number="0987654321",
            password="securepassword"
        )
        label = Label.objects.create(
            user=user,
            name="Personal"
        )
        note = Note.objects.create(
            user=user,
            label=label,
            title="My First Note",
            content="This is the content of my first note."
        )
        
        assert note.title == "My First Note"
        assert note.content == "This is the content of my first note."
        assert note.user == user
        assert note.label == label
        assert not note.is_archived
        assert not note.is_pinned
        assert str(note) == "My First Note"


@pytest.mark.django_db
class TestNotesAPI:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create(
            name="API Note User",
            email="apinoteuser@example.com",
            phone_number="1122334455",
            password="securepassword",
            is_email_verified=True
        )
        self.notes_url = reverse('api-notes')

    def test_get_notes_unauthorized(self):
        response = self.client.get(self.notes_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED # type: ignore


