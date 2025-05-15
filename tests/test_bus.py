import pytest
from unittest.mock import MagicMock, patch
import asyncio
import datetime

from activity_bus.bus import ActivityBus
from activity_bus.errors import InvalidActivityError, ActivityIdError
from activity_bus.registry import registry


# Mock ActivityStore for testing
class MockActivityStore:
    def __init__(self):
        self.stored_activities = {}
        self.collections = {"/sys/rules": [], "/sys/effects": []}
    
    async def store(self, activity, collection=None):
        activity_id = activity.get("id")
        if activity_id:
            if collection:
                if collection not in self.collections:
                    self.collections[collection] = []
                self.collections[collection].append(activity)
            else:
                self.stored_activities[activity_id] = activity
        return activity
    
    async def query(self, query, collection=None):
        if collection:
            return self.collections.get(collection, [])
        return list(self.stored_activities.values())
    
    async def dereference(self, activity):
        return activity
    
    async def frame(self, activity, pattern, require_match=False):
        # Simple matching logic for testing
        for key, value in pattern.items():
            if key not in activity or activity[key] != value:
                if require_match:
                    return False
                else:
                    return None
        return activity
    
    async def convert_to_tombstone(self, activity):
        tombstone = {
            "id": activity["id"],
            "type": "Tombstone",
            "formerType": activity.get("type", "Unknown"),
            "deleted": datetime.datetime.utcnow().isoformat() + "Z"
        }
        self.stored_activities[activity["id"]] = tombstone
        return tombstone


@pytest.fixture
def mock_store():
    return MockActivityStore()


@pytest.fixture
def bus(mock_store):
    return ActivityBus(store=mock_store, namespace="https://example.com")


@pytest.mark.asyncio
async def test_activity_bus_init():
    """Test ActivityBus initialization."""
    # Test with provided store
    mock_store = MockActivityStore()
    bus = ActivityBus(store=mock_store, namespace="https://example.com")
    assert bus.store == mock_store
    assert bus.namespace == "https://example.com"
    assert isinstance(bus.queue, asyncio.Queue)
    
    # Test without namespace
    bus = ActivityBus(store=mock_store)
    assert bus.namespace is None


@pytest.mark.asyncio
async def test_submit_valid_activity(bus):
    """Test submitting a valid activity."""
    activity = {
        "type": "Create",
        "actor": "test-user"
    }
    
    result = await bus.submit(activity)
    
    # Check ID was generated
    assert "id" in result
    assert result["id"].startswith("https://example.com/users/test-user/outbox/")
    
    # Check timestamp was added
    assert "published" in result
    
    # Check result field was initialized
    assert "result" in result
    assert result["result"] == []
    
    # Check activity was stored
    assert result["id"] in bus.store.stored_activities
    
    # Check activity was enqueued
    queued_activity = await bus.queue.get()
    assert queued_activity == result


@pytest.mark.asyncio
async def test_submit_with_existing_id(bus):
    """Test submitting an activity with an existing ID."""
    activity = {
        "type": "Create",
        "actor": "test-user",
        "id": "https://example.com/users/test-user/outbox/existing-id"
    }
    
    result = await bus.submit(activity)
    
    # Check ID was preserved
    assert result["id"] == "https://example.com/users/test-user/outbox/existing-id"
    
    # Check activity was stored with the existing ID
    assert "https://example.com/users/test-user/outbox/existing-id" in bus.store.stored_activities


@pytest.mark.asyncio
async def test_submit_invalid_activity(bus):
    """Test submitting invalid activities."""
    # Missing actor
    with pytest.raises(InvalidActivityError):
        await bus.submit({"type": "Create"})
    
    # Missing type
    with pytest.raises(InvalidActivityError):
        await bus.submit({"actor": "test-user"})
    
    # Not a dictionary
    with pytest.raises(InvalidActivityError):
        await bus.submit("not a dictionary")


@pytest.mark.asyncio
async def test_submit_invalid_id(bus):
    """Test submitting an activity with an invalid ID scope."""
    activity = {
        "type": "Create",
        "actor": "test-user",
        "id": "https://wrong-domain.com/users/test-user/outbox/bad-id"
    }
    
    with pytest.raises(ActivityIdError):
        await bus.submit(activity)


@pytest.mark.asyncio
async def test_process_next_empty_queue(bus):
    """Test processing from an empty queue."""
    # Queue is empty
    result = await bus.process_next()
    assert result is None


@pytest.mark.asyncio
async def test_process_activity(bus, mock_store):
    """Test processing an activity with matching rules."""
    # Register a test effect
    def test_effect(activity):
        if "result" not in activity:
            activity["result"] = []
        activity["result"].append({"type": "Note", "content": "Effect executed"})
        return {"type": "Log", "message": "Effect log"}
    
    registry.register("test.effect", test_effect)
    
    # Add a rule
    rule = {
        "id": "test.rule",
        "match": {"type": "Create"},
        "effect": ["test.effect"],
        "priority": 100,
        "type": "Rule"
    }
    await mock_store.store(rule, collection="/sys/rules")
    
    # Create and submit an activity
    activity = {
        "type": "Create",
        "actor": "test-user",
        "object": {"type": "Note", "content": "Test content"}
    }
    
    submitted = await bus.submit(activity)
    processed = await bus.process_next()
    
    # Check that effect was executed
    assert len(processed["result"]) == 2  # Effect result and effect log
    assert processed["result"][0]["type"] == "Note"
    assert processed["result"][0]["content"] == "Effect executed"
    assert processed["result"][1]["type"] == "Log"
    assert processed["result"][1]["message"] == "Effect log"
    
    # Check that processed activity was stored
    assert submitted["id"] in mock_store.stored_activities
    stored = mock_store.stored_activities[submitted["id"]]
    assert len(stored["result"]) == 2


@pytest.mark.asyncio
async def test_process_error_handling(bus, mock_store):
    """Test error handling during processing."""
    # Register an effect that raises an exception
    def error_effect(activity):
        raise Exception("Test error")
    
    registry.register("test.error_effect", error_effect)
    
    # Add a rule
    rule = {
        "id": "test.error.rule",
        "match": {"type": "Create"},
        "effect": ["test.error_effect"],
        "priority": 100,
        "type": "Rule"
    }
    await mock_store.store(rule, collection="/sys/rules")
    
    # Create and submit an activity
    activity = {
        "type": "Create",
        "actor": "test-user",
        "object": {"type": "Note", "content": "Test content"}
    }
    
    submitted = await bus.submit(activity)
    processed = await bus.process_next()
    
    # Check that activity was converted to a tombstone
    assert processed["type"] == "Tombstone"
    assert processed["formerType"] == "Create"
    assert "deleted" in processed
    
    # Check that the error was recorded
    assert submitted["id"] in mock_store.stored_activities
    stored = mock_store.stored_activities[submitted["id"]]
    assert stored["type"] == "Tombstone"


@pytest.mark.asyncio
async def test_load_rules(bus, mock_store):
    """Test loading rules."""
    with patch("activity_bus.rules.load_rules") as mock_load_rules:
        mock_load_rules.return_value = [
            {
                "id": "test.rule1",
                "match": {"type": "Create"},
                "effect": ["test.effect1"],
                "type": "Rule"
            },
            {
                "id": "test.rule2",
                "match": {"type": "Update"},
                "effect": ["test.effect2"],
                "type": "Rule"
            }
        ]
        
        rules = await bus.load_rules("/path/to/rules")
        
        # Check that rules were loaded and stored
        assert len(rules) == 2
        assert len(mock_store.collections["/sys/rules"]) == 2
        
        # Check correct parameters were passed
        mock_load_rules.assert_called_once_with("/path/to/rules")


@pytest.mark.asyncio
async def test_load_effects(bus, mock_store):
    """Test loading effects."""
    with patch("activity_bus.effects.load_effects") as mock_load_effects:
        mock_load_effects.return_value = [
            {
                "id": "test.module.effect1",
                "priority": 100,
                "type": "Effect"
            },
            {
                "id": "test.module.effect2",
                "priority": 50,
                "type": "Effect"
            }
        ]
        
        effects = await bus.load_effects("test.module")
        
        # Check that effects were loaded and stored
        assert len(effects) == 2
        assert len(mock_store.collections["/sys/effects"]) == 2
        
        # Check correct parameters were passed
        mock_load_effects.assert_called_once_with("test.module")