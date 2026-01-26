"""
Custom exceptions for Stellax applications.
"""


class StellaxError(Exception):
    """Base exception for Stellax applications."""

    pass


class PermissionDeniedError(StellaxError):
    """Raised when a user tries to access a resource they don't own."""

    pass


class ValidationError(StellaxError):
    """Raised when data validation fails in the service layer."""

    pass


class NotFoundError(StellaxError):
    """Raised when a requested resource is not found."""

    pass


class ConfigurationError(StellaxError):
    """Raised when there's a configuration issue."""

    pass
