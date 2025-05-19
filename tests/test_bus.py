"""
Tests for the ActivityBus core class.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from activity_bus.behaviors import registry, when
from activity_bus.bus import ActivityBus
from activity_bus.errors import ActivityIdError, InvalidActivityError


# Clear registry before each test
@pytest.fixture(autouse=True)
def clear_registry():
    registry.clear()
    yield


@pytest.fixture
def mock_store():
    """Create a mock ActivityStore."""
    store = AsyncMock()
    store.store = AsyncMock(return_value=None)
    store.dereference = AsyncMock(return_value=None)
    store.convert_to_tombstone = AsyncMock(
        side_effect=lambda x: {
            "type": "Tombstone",
            "formerType": x.get("type", "Unknown"),
            "id": x.get("id", "unknown-id"),
            "deleted": "2023-01-01T00:00:00Z",
        }
    )
    return store


@pytest.fixture
def bus(mock_store):
    """Create an ActivityBus with a mock store."""
    return ActivityBus(store=mock_store)


@pytest.mark.asyncio
async def test_init():
    """Test initialization of the ActivityBus."""
    # Default initialization
    bus = ActivityBus()

    # Should create an asyncio.Queue
    assert isinstance(bus.queue, asyncio.Queue)

    # Should have a default store
    assert bus.store is not None

    # Should have a default namespace
    assert bus.namespace == "activity_bus"

    # Custom initialization
    mock_store = MagicMock()
    custom_namespace = "custom_namespace"

    bus = ActivityBus(store=mock_store, namespace=custom_namespace)

    # Should use the provided store
    assert bus.store is mock_store

    # Should use the provided namespace
    assert bus.namespace == custom_namespace


@pytest.mark.asyncio
async def test_submit_valid_activity(bus, mock_store):
    """Test submitting a valid activity."""
    # Create a valid activity
    activity = {
        "type": "Create",
        "actor": "https://example.com/users/123",
        "object": {"type": "Note", "content": "This is a test note"},
    }

    # Submit the activity
    result = await bus.submit(activity)

    # Should return a valid activity with additional fields
    assert result["type"] == "Create"
    assert result["actor"] == "https://example.com/users/123"
    assert "id" in result
    assert "published" in result
    assert "result" in result

    # Should store the activity
    mock_store.store.assert_called_once()

    # Should enqueue the activity
    assert bus.queue.qsize() == 1


@pytest.mark.asyncio
async def test_submit_with_existing_id(bus, mock_store):
    """Test submitting an activity with an existing ID."""
    # Create a valid activity with an ID
    activity_id = "/users/123/outbox/abcdef123456"
    activity = {
        "type": "Create",
        "actor": "https://example.com/users/123",
        "id": activity_id,
        "object": {"type": "Note", "content": "This is a test note"},
    }

    # Submit the activity
    result = await bus.submit(activity)

    # Should keep the existing ID
    assert result["id"] == activity_id

    # Should store the activity
    mock_store.store.assert_called_once()

    # Should enqueue the activity
    assert bus.queue.qsize() == 1


@pytest.mark.asyncio
async def test_submit_invalid_activity_missing_actor(bus):
    """Test submitting an invalid activity missing an actor."""
    # Create an invalid activity (missing actor)
    activity = {
        "type": "Create",
        "object": {"type": "Note", "content": "This is a test note"},
    }

    # Submit the activity - should raise InvalidActivityError
    with pytest.raises(InvalidActivityError) as excinfo:
        await bus.submit(activity)

    # Verify the error message
    assert "must contain an 'actor' field" in str(excinfo.value)

    # Should not store or enqueue the activity
    assert not bus.store.store.called
    assert bus.queue.qsize() == 0


@pytest.mark.asyncio
async def test_submit_invalid_activity_missing_type(bus):
    """Test submitting an invalid activity missing a type."""
    # Create an invalid activity (missing type)
    activity = {
        "actor": "https://example.com/users/123",
        "object": {"type": "Note", "content": "This is a test note"},
    }

    # Submit the activity - should raise InvalidActivityError
    with pytest.raises(InvalidActivityError) as excinfo:
        await bus.submit(activity)

    # Verify the error message
    assert "must contain a 'type' field" in str(excinfo.value)

    # Should not store or enqueue the activity
    assert not bus.store.store.called
    assert bus.queue.qsize() == 0


@pytest.mark.asyncio
async def test_submit_invalid_id_scope(bus):
    """Test submitting an activity with an invalid ID scope."""
    # Create an activity with an invalid ID scope
    activity = {
        "type": "Create",
        "actor": "https://example.com/users/123",
        "id": "/users/456/outbox/abcdef123456",  # Different user ID
        "object": {"type": "Note", "content": "This is a test note"},
    }

    # Submit the activity - should raise ActivityIdError
    with pytest.raises(ActivityIdError) as excinfo:
        await bus.submit(activity)

    # Verify the error message
    assert "not properly scoped under actor" in str(excinfo.value)

    # Should not store or enqueue the activity
    assert not bus.store.store.called
    assert bus.queue.qsize() == 0


@pytest.mark.asyncio
async def test_process_next_empty_queue(bus):
    """Test processing the next activity when the queue is empty."""
    # Queue is empty
    assert bus.queue.qsize() == 0

    # Process the next activity
    result = await bus.process_next()

    # Should return None
    assert result is None

    # Should not process any activities
    assert not bus.store.store.called


@pytest.mark.asyncio
async def test_process_next_with_activity(bus, mock_store):
    """Test processing the next activity in the queue."""
    # Create a valid activity
    activity = {
        "type": "Create",
        "actor": "https://example.com/users/123",
        "id": "/users/123/outbox/abcdef123456",
        "object": {"type": "Note", "content": "This is a test note"},
        "result": [],
    }

    # Add the activity to the queue
    await bus.queue.put(activity)

    # Register a test behavior
    @when({"type": "Create", "object": {"type": "Note"}})
    def test_behavior(act):
        act["result"].append({"type": "Log", "content": "Processed by test behavior"})
        return None

    result = await bus.process_next()

    # Should return the processed activity
    assert result is not None
    assert result["type"] == "Create"
    assert result["id"] == "/users/123/outbox/abcdef123456"

    # Should have processed the activity with the behavior
    assert len(result["result"]) == 1
    assert result["result"][0]["type"] == "Log"
    assert result["result"][0]["content"] == "Processed by test behavior"

    # Should have stored the processed activity
    mock_store.store.assert_called()

    # Queue should be empty
    assert bus.queue.qsize() == 0


@pytest.mark.asyncio
async def test_process_with_exception(bus, mock_store):
    """Test processing an activity that causes an exception."""
    # Create a valid activity
    activity = {
        "type": "Create",
        "actor": "https://example.com/users/123",
        "id": "/users/123/outbox/abcdef123456",
        "object": {"type": "Note", "content": "This is a test note"},
        "result": [],
    }

    # Register a test behavior that raises an exception
    @when({"type": "Create", "object": {"type": "Note"}})
    def test_behavior(act):
        raise ValueError("Test exception")

    result = await bus.process(activity)

    # Should return a tombstone
    assert result["type"] == "Tombstone"
    assert result["formerType"] == "Create"
    assert result["id"] == "/users/123/outbox/abcdef123456"

    # Should have added an error to the original activity
    assert len(activity["result"]) == 1
    assert activity["result"][0]["type"] == "Error"
    assert "ValueError: Test exception" in activity["result"][0]["content"]

    # Should have converted the activity to a tombstone
    mock_store.convert_to_tombstone.assert_called_once_with(activity)

    # Should have stored the tombstone
    assert mock_store.store.call_count == 1


@pytest.mark.asyncio
async def test_extract_user_id_string():
    """Test extracting a user ID from an actor URI string."""
    bus = ActivityBus()

    # Test with various actor URIs
    assert bus._extract_user_id("https://example.com/users/123") == "123"
    assert bus._extract_user_id("https://example.com/users/alice") == "alice"
    assert bus._extract_user_id("https://example.com/users/bob/") == "bob"


@pytest.mark.asyncio
async def test_extract_user_id_object():
    """Test extracting a user ID from an actor object with an ID."""
    bus = ActivityBus()

    # Test with an actor object
    actor = {"id": "https://example.com/users/123"}
    assert bus._extract_user_id(actor) == "123"


@pytest.mark.asyncio
async def test_extract_user_id_invalid():
    """Test extracting a user ID from an invalid actor."""
    bus = ActivityBus()

    # Test with an invalid actor
    with pytest.raises(InvalidActivityError) as excinfo:
        bus._extract_user_id(123)

    # Verify the error message
    assert "Actor must be a string or have an 'id' field" in str(excinfo.value)
