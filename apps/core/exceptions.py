"""
Custom exceptions for Teachka applications.
"""


class TeachkaError(Exception):
    """Base exception for Teachka applications."""

    pass


class PermissionDeniedError(TeachkaError):
    """Raised when a user tries to access a resource they don't own."""

    pass


class ValidationError(TeachkaError):
    """Raised when data validation fails in the service layer."""

    pass


class NotFoundError(TeachkaError):
    """Raised when a requested resource is not found."""

    pass


class ConfigurationError(TeachkaError):
    """Raised when there's a configuration issue."""

    pass
