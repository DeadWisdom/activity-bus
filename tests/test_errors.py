"""
Tests for the errors module.
"""

from activity_bus.errors import (
    ActivityBusError,
    ActivityIdError,
    BehaviorExecutionError,
    BehaviorRegistrationError,
    InvalidActivityError,
)


def test_error_hierarchy():
    """Test that the error hierarchy is structured correctly."""
    # ActivityBusError is the base class
    assert issubclass(InvalidActivityError, ActivityBusError)
    assert issubclass(ActivityIdError, InvalidActivityError)
    assert issubclass(BehaviorExecutionError, ActivityBusError)
    assert issubclass(BehaviorRegistrationError, ActivityBusError)

    # ActivityIdError is a subclass of InvalidActivityError
    assert issubclass(ActivityIdError, InvalidActivityError)

    # Each error can be instantiated with a message
    error_msg = "Test error message"

    error = ActivityBusError(error_msg)
    assert str(error) == error_msg

    error = InvalidActivityError(error_msg)
    assert str(error) == error_msg

    error = ActivityIdError(error_msg)
    assert str(error) == error_msg

    error = BehaviorExecutionError(error_msg)
    assert str(error) == error_msg

    error = BehaviorRegistrationError(error_msg)
    assert str(error) == error_msg
