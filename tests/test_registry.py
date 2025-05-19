"""
Tests for the registry module.
"""

from unittest.mock import Mock

from activity_bus.registry import BehaviorRegistry


def test_registry_register_and_get():
    """Test registering and retrieving behavior functions."""
    registry = BehaviorRegistry()

    # Create a mock function
    mock_func = Mock()

    # Register the mock
    behavior_id = "/sys/behaviors/test.mock_func"
    registry.register(behavior_id, mock_func)

    # Retrieve the registered function
    retrieved_func = registry.get(behavior_id)

    # Verify it's the same function
    assert retrieved_func is mock_func

    # Test getting a non-existent behavior
    assert registry.get("non_existent_id") is None


def test_registry_all_behaviors():
    """Test getting all registered behaviors."""
    registry = BehaviorRegistry()

    # Create and register multiple mock functions
    mock_func1 = Mock()
    mock_func2 = Mock()

    behavior_id1 = "/sys/behaviors/test.mock_func1"
    behavior_id2 = "/sys/behaviors/test.mock_func2"

    registry.register(behavior_id1, mock_func1)
    registry.register(behavior_id2, mock_func2)

    # Get all behaviors
    all_behaviors = registry.all_behaviors()

    # Verify all registered behaviors are returned
    assert len(all_behaviors) == 2
    assert all_behaviors[behavior_id1] is mock_func1
    assert all_behaviors[behavior_id2] is mock_func2


def test_registry_clear():
    """Test clearing the registry."""
    registry = BehaviorRegistry()

    # Register a mock function
    mock_func = Mock()
    behavior_id = "/sys/behaviors/test.mock_func"
    registry.register(behavior_id, mock_func)

    # Verify it's registered
    assert registry.get(behavior_id) is mock_func

    # Clear the registry
    registry.clear()

    # Verify it's cleared
    assert registry.get(behavior_id) is None
    assert len(registry.all_behaviors()) == 0
