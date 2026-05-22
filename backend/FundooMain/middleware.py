import time
import logging
from collections import defaultdict

from common.api_response import build_api_response, get_message_from_payload

logger = logging.getLogger(__name__)


class RequestExecutionTimeMiddleware:

    # Global dictionary to store API hit counts
    api_hit_counts = defaultdict(int)

    def __init__(self, get_response):
        """
        Runs only once when the server starts.
        """
        self.get_response = get_response

    def __call__(self, request):

        # Start execution timer
        start_time = time.time()

        # Pass request to next middleware or view
        response = self.get_response(request)

        # Calculate execution duration
        duration = time.time() - start_time

        # Request details
        path = request.path
        method = request.method.upper()

        # Track only selected APIs
        if self._should_track(request):

            # Unique API key
            endpoint_key = f"{method} {path}"

            # Increase hit count
            self.api_hit_counts[endpoint_key] += 1

            # Current hit count
            current_count = self.api_hit_counts[endpoint_key]

            # Individual API log
            print(
                f"[Middleware Log] "
                f"{endpoint_key} | "
                f"Hits: {current_count} | "
                f"Time: {duration:.4f} sec"
            )

            # Print grouped summary
            print("\n=== API HIT COUNTS ===")

            for api, count in self.api_hit_counts.items():
                print(f"{api} -> {count}")

            print("======================\n")

        if self._should_wrap_response(request, response):
            response.data = build_api_response(
                self._get_response_message(request, response.data),
                response.data,
                response.status_code,
            )

        return response

    def _should_track(self, request):
        """
        Decide which requests should be tracked.
        """

        # Ignore browser preflight requests
        if request.method == 'OPTIONS':
            return False

        # Track only API routes
        if not request.path.startswith('/api/'):
            return False

        # Ignore documentation/debug routes
        ignored_routes = {
            '/api/schema/',
            '/api/docs/',
            '/api/redoc/',
            '/api/debug/session-hit-counts/'
        }

        if request.path in ignored_routes:
            return False

        return True

    def _should_wrap_response(self, request, response):
        if request.method == 'OPTIONS':
            return False

        if not request.path.startswith('/api/'):
            return False

        if not hasattr(response, 'data'):
            return False

        if response.status_code == 204:
            return False

        payload = response.data
        if isinstance(payload, dict) and {'message', 'payload', 'status code'} <= set(payload.keys()):
            return False

        return True

    def _get_response_message(self, request, payload):
        resolver_match = getattr(request, 'resolver_match', None)
        if resolver_match is not None:
            view_func = getattr(resolver_match, 'func', None)
            view_class = getattr(view_func, 'view_class', None)
            if view_class is not None:
                response_messages = getattr(view_class, 'response_messages', {})
                if isinstance(response_messages, dict):
                    message = response_messages.get(request.method.upper())
                    if isinstance(message, str) and message:
                        return message

                response_message = getattr(view_class, 'response_message', None)
                if isinstance(response_message, str) and response_message:
                    return response_message

        return get_message_from_payload(payload)