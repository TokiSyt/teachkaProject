import logging
import uuid

from django.conf import settings

logger = logging.getLogger(__name__)


class RequestIdMiddleware:
    """Attach a unique request ID to each request and log it."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        request.request_id = request_id
        response = self.get_response(request)
        response["X-Request-Id"] = request_id
        return response


class SecurityHeadersMiddleware:
    """Add CSP and referrer policy headers to every response."""

    CSP = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "img-src 'self' data: blob: https://res.cloudinary.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not settings.DEBUG:
            response.setdefault("Content-Security-Policy", self.CSP)
            response.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return response
