"""
This module contains custom exceptions for the Activity Bus library.
"""

class ActivityBusError(Exception):
    """Base exception for all Activity Bus related errors."""
    pass


class InvalidActivityError(ActivityBusError):
    """Raised when an activity is invalid or missing required fields."""
    pass


class ActivityIdError(InvalidActivityError):
    """Raised when an activity ID is invalid or improperly scoped."""
    pass


class BehaviorExecutionError(ActivityBusError):
    """Raised when there's an error executing a behavior."""
    pass


class BehaviorRegistrationError(ActivityBusError):
    """Raised when there's an error registering a behavior."""
    pass
