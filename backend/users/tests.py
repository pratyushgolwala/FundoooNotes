import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User

@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self):
        user = User.objects.create(
            name="Test User",
            email="test@example.com",
            phone_number="1234567890",
            password="securepassword"
        )
        assert user.name == "Test User"
        assert str(user) == "Test User"


@pytest.mark.django_db
class TestUserAPI:
    def setup_method(self):
        self.client = APIClient()
        self.signup_url = reverse('api-signup')
        self.login_url = reverse('api-login')

    def test_user_signup_api(self, mocker):
        # We mock send_verification_email so celery isn't triggered in tests
        mock_send_email = mocker.patch("users.api_views.send_verification_email.delay")
        
        payload = {
            "username": "api_user",
            "email": "apiuser@example.com",
            "phone_number": "1122334455",
            "password": "password123"
        }
        
        response = self.client.post(self.signup_url, payload, format="json")
        
        assert response.status_code == status.HTTP_201_CREATED
        assert "user_id" in response.data
        assert "Account created successfully" in response.data["detail"]
        
        # Check database
        user = User.objects.get(email="apiuser@example.com")
        assert user.name == "api_user"
        
        # Verify celery task was dispatched
        mock_send_email.assert_called_once_with(user.pk)

