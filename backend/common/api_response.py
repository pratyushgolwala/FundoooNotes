from typing import Any

from rest_framework.response import Response
from rest_framework.views import APIView


def build_api_response(message: str, payload: Any, status_code: int) -> dict[str, Any]:
    return {
        "message": message,
        "payload": payload,
        "status code": status_code,
    }


def get_message_from_payload(payload: Any, default: str = "Success") -> str:
    if isinstance(payload, dict):
        detail = payload.get("detail")
        if isinstance(detail, str) and detail:
            return detail

        message = payload.get("message")
        if isinstance(message, str) and message:
            return message

    return default


class EnvelopeAPIView(APIView):
    response_messages: dict[str, str] = {}

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)

        if not isinstance(response, Response):
            return response

        if response.status_code == 204:
            return response

        payload = response.data
        if isinstance(payload, dict) and {'message', 'payload', 'status code'} <= set(payload.keys()):
            return response

        response.data = build_api_response(
            self._get_response_message(request, payload),
            payload,
            response.status_code,
        )
        return response

    def _get_response_message(self, request, payload):
        response_messages = getattr(self, "response_messages", {})
        if isinstance(response_messages, dict):
            message = response_messages.get(request.method.upper())
            if isinstance(message, str) and message:
                return message

        response_message = getattr(self, "response_message", None)
        if isinstance(response_message, str) and response_message:
            return response_message

        return get_message_from_payload(payload)
