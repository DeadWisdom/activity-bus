"""
Tests for the behaviors module.
"""

import pytest

from activity_bus.behaviors import get_all_behaviors, when
from activity_bus.registry import registry


# Clear registry before each test
@pytest.fixture(autouse=True)
def clear_registry():
    registry.clear()
    yield


def test_when_decorator():
    """Test that the when decorator registers behaviors correctly."""
    # Define a test pattern
    test_pattern = {"type": "Test", "actor": {"@exists": True}}

    # Define a test function using the when decorator
    @when(test_pattern)
    def test_function(activity):
        return activity

    # The function should be registered in the registry
    behavior_id = "/sys/behaviors/test_behaviors.test_function"
    registered_func = registry.get(behavior_id)

    # Verify the function is registered
    assert registered_func is not None
    assert registered_func is test_function

    # Verify the pattern is attached to the function
    assert hasattr(registered_func, '_when_pattern')
    assert registered_func._when_pattern == test_pattern

    # Verify the behavior ID is attached to the function
    assert hasattr(registered_func, '_behavior_id')
    assert registered_func._behavior_id == behavior_id


def test_when_decorator_with_custom_id():
    """Test that the when decorator supports custom behavior IDs."""
    # Define a test pattern
    test_pattern = {"type": "Test", "actor": {"@exists": True}}

    # Define a custom behavior ID
    custom_id = "/sys/behaviors/custom/my_test_behavior"

    # Define a test function using the when decorator with a custom ID
    @when(test_pattern, id=custom_id)
    def test_function(activity):
        return activity

    # The function should be registered in the registry with the custom ID
    registered_func = registry.get(custom_id)

    # Verify the function is registered
    assert registered_func is not None
    assert registered_func is test_function

    # Verify the pattern is attached to the function
    assert hasattr(registered_func, '_when_pattern')
    assert registered_func._when_pattern == test_pattern

    # Verify the behavior ID is attached to the function
    assert hasattr(registered_func, '_behavior_id')
    assert registered_func._behavior_id == custom_id


def test_get_all_behaviors():
    """Test retrieving all registered behaviors."""
    # Define test patterns
    pattern1 = {"type": "Test1"}
    pattern2 = {"type": "Test2"}

    # Define test functions using the when decorator
    @when(pattern1)
    def test_function1(activity):
        return activity

    @when(pattern2)
    def test_function2(activity):
        return activity

    # Get all behaviors
    behaviors = get_all_behaviors()

    # Verify both behaviors are returned
    assert len(behaviors) == 2

    # Get behavior IDs
    behavior_id1 = "/sys/behaviors/test_behaviors.test_function1"
    behavior_id2 = "/sys/behaviors/test_behaviors.test_function2"

    # Verify behavior1
    assert behavior_id1 in behaviors
    assert behaviors[behavior_id1]["id"] == behavior_id1
    assert behaviors[behavior_id1]["type"] == "Behavior"
    assert behaviors[behavior_id1]["when"] == pattern1
    assert behaviors[behavior_id1]["_function"] == test_function1

    # Verify behavior2
    assert behavior_id2 in behaviors
    assert behaviors[behavior_id2]["id"] == behavior_id2
    assert behaviors[behavior_id2]["type"] == "Behavior"
    assert behaviors[behavior_id2]["when"] == pattern2
    assert behaviors[behavior_id2]["_function"] == test_function2


def test_behavior_execution():
    """Test that the decorated function can still be executed."""
    # Define a test pattern
    test_pattern = {"type": "Test"}

    # Define a test function using the when decorator
    @when(test_pattern)
    def test_function(activity):
        activity["processed"] = True
        return activity

    # Create a test activity
    test_activity = {"type": "Test", "actor": "test-actor"}

    # Execute the function
    result = test_function(test_activity)

    # Verify the function processed the activity
    assert result["processed"] is True
