import jwt
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import UserRateThrottle

from drf_spectacular.utils import extend_schema

from common.api_response import EnvelopeAPIView
from users.models import User
from .models import Label
from .serializers import LabelSerializer


class LabelsRateThrottle(UserRateThrottle):
    scope = "notes"


def _get_bearer_token(request):
    """Extract JWT token from Authorization header"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip()


def _decode_token(token):
    """Decode JWT token"""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])


def _get_user_from_request(request):
    """Extract user from JWT token in request"""
    token = _get_bearer_token(request)
    if not token:
        return None, Response(
            {"detail": "Missing Bearer token"}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    try:
        payload = _decode_token(token)
        user_id = payload.get("user_id")
        user = User.objects.filter(pk=user_id).first()
        if not user:
            return None, Response(
                {"detail": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        return user, None
    except jwt.ExpiredSignatureError:
        return None, Response(
            {"detail": "Token expired"}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    except jwt.InvalidTokenError:
        return None, Response(
            {"detail": "Invalid token"}, 
            status=status.HTTP_401_UNAUTHORIZED
        )


class LabelsAPI(EnvelopeAPIView):
    throttle_classes = [LabelsRateThrottle]
    response_messages = {
        "GET": "Labels fetched",
        "POST": "Label created",
    }

    @extend_schema(responses={200: LabelSerializer(many=True)})
    def get(self, request):
        """Get all labels for authenticated user"""
        user, error_response = _get_user_from_request(request)
        if error_response:
            return error_response
        
        labels = Label.objects.filter(user=user).order_by('name')
        serializer = LabelSerializer(labels, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=LabelSerializer, responses={201: LabelSerializer})
    def post(self, request):
        """Create a new label"""
        user, error_response = _get_user_from_request(request)
        if error_response:
            return error_response
        
        serializer = LabelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)