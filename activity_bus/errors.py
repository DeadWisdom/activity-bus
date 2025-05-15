# ABOUTME: Defines error classes used throughout the activity_bus package 
# ABOUTME: Provides specific exceptions for different error conditions

class ActivityBusError(Exception):
    """Base exception class for all Activity Bus errors."""
    pass


class InvalidActivityError(ActivityBusError):
    """Raised when an activity doesn't meet the required structure."""
    pass


class ActivityIdError(ActivityBusError):
    """Raised when there's an issue with activity ID generation or validation."""
    pass


class EffectExecutionError(ActivityBusError):
    """Raised when an effect fails to execute properly."""
    pass


class RuleMatchError(ActivityBusError):
    """Raised when there's an issue with rule matching."""
    pass


class RuleLoadError(ActivityBusError):
    """Raised when there's an issue loading rules from files."""
    pass


class EffectLoadError(ActivityBusError):
    """Raised when there's an issue loading effects from modules."""
    pass