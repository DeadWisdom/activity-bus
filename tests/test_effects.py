import sys
from unittest.mock import patch

import pytest

from activity_bus.effects import effect, load_effects
from activity_bus.errors import EffectLoadError
from activity_bus.registry import registry


# Clear registry before tests
@pytest.fixture(autouse=True)
def clear_registry():
    registry.effects = {}
    yield


def test_effect_decorator() -> None:
    """Test the effect decorator correctly registers a function."""

    @effect(priority=50, description="Test effect")
    def test_function(activity):
        return activity

    expected_id = f"{__name__}.test_function"
    assert expected_id in registry.effects

    effect_data = registry.effects[expected_id]
    assert effect_data["function"] == test_function
    assert effect_data["priority"] == 50
    assert effect_data["description"] == "Test effect"
    assert effect_data["type"] == "Effect"

    # Test the function still works
    test_activity = {"type": "Test"}
    assert test_function(test_activity) == test_activity


@pytest.mark.asyncio
async def test_load_effects() -> None:
    """Test loading effects from modules."""

    # Clear registry before this specific test
    registry.effects = {}

    # Create a mock module with effects
    mock_module = type("module", (), {})

    # Create and register effect directly with correct module name
    def mock_effect(activity):
        return activity

    # Set the module name
    mock_effect.__module__ = "test_module"
    mock_effect.__name__ = "mock_effect"

    # Register the effect directly in the registry
    registry.register(effect_id="test_module.mock_effect", func=mock_effect, priority=50)

    # Store the effect in the mock module
    mock_module.mock_effect = mock_effect

    with patch.dict(sys.modules, {"test_module": mock_module}):
        # Test successful loading
        effects = await load_effects("test_module")
        assert len(effects) == 1
        assert effects[0]["id"] == "test_module.mock_effect"

        # Test loading non-existent module
        with pytest.raises(EffectLoadError):
            await load_effects("nonexistent_module")
