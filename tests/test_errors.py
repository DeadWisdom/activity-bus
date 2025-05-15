import pytest

from activity_bus.errors import (
    ActivityBusError,
    InvalidActivityError,
    ActivityIdError,
    EffectExecutionError,
    RuleMatchError,
    RuleLoadError,
    EffectLoadError,
)


def test_activity_bus_error():
    """Test that ActivityBusError can be raised and caught."""
    with pytest.raises(ActivityBusError):
        raise ActivityBusError("Test error")


def test_error_inheritance():
    """Test that all errors inherit from ActivityBusError."""
    error_classes = [
        InvalidActivityError,
        ActivityIdError,
        EffectExecutionError,
        RuleMatchError,
        RuleLoadError,
        EffectLoadError,
    ]
    
    for error_class in error_classes:
        error = error_class("Test error")
        assert isinstance(error, ActivityBusError)
        
        # Make sure the error message is preserved
        assert str(error) == "Test error"