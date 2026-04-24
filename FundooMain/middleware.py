import time
import logging

logger = logging.getLogger(__name__)

class RequestExecutionTimeMiddleware:
    def __init__(self, get_response):
        # One-time configuration and initialization when the server starts.
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request BEFORE the view is called.
        start_time = time.time()

        # The request passes to the next middleware or the view
        response = self.get_response(request)

        # Code to be executed for each request AFTER the view is called.
        duration = time.time() - start_time
        path = request.path
        method = request.method
        
        # Log the execution time
        print(f"[Middleware Log] {method} {path} took {duration:.4f} seconds")

        return response