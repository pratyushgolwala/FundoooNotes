import pytest
from labels.models import Label
from users.models import User

@pytest.mark.django_db
class TestLabelModel:
    def test_create_label(self):
        user = User.objects.create(
            name="Test User",
            email="testuser@example.com",
            phone_number="1234567890",
            password="testpassword"
        )
        label = Label.objects.create(
            user=user,
            name="Work"
        )
        assert label.name == "Work"
        assert label.user == user
        assert str(label) == "Work"

