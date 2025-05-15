import pytest

from activity_bus.registry import Registry


def test_registry_initialization():
    """Test that a new Registry is initialized with an empty effects dict."""
    registry = Registry()
    assert registry.effects == {}


def test_registry_register():
    """Test registering an effect in the registry."""
    registry = Registry()
    
    def test_effect(activity):
        return activity
    
    effect_data = registry.register(
        effect_id="test.effect",
        func=test_effect,
        priority=50,
        description="Test effect"
    )
    
    assert "test.effect" in registry.effects
    assert registry.effects["test.effect"]["function"] == test_effect
    assert registry.effects["test.effect"]["priority"] == 50
    assert registry.effects["test.effect"]["description"] == "Test effect"
    assert registry.effects["test.effect"]["type"] == "Effect"
    assert registry.effects["test.effect"] == effect_data


def test_registry_get():
    """Test getting an effect from the registry."""
    registry = Registry()
    
    def test_effect(activity):
        return activity
    
    registry.register(
        effect_id="test.effect",
        func=test_effect
    )
    
    effect = registry.get("test.effect")
    assert effect["function"] == test_effect
    
    # Non-existent effect
    assert registry.get("nonexistent.effect") is None


def test_registry_list_effects():
    """Test listing all effects in the registry."""
    registry = Registry()
    
    def test_effect1(activity):
        return activity
    
    def test_effect2(activity):
        return activity
    
    registry.register(
        effect_id="test.effect1",
        func=test_effect1,
        priority=50
    )
    
    registry.register(
        effect_id="test.effect2",
        func=test_effect2,
        priority=100
    )
    
    effects = registry.list_effects()
    assert len(effects) == 2
    
    # Function references should be removed
    for effect in effects:
        assert "function" not in effect