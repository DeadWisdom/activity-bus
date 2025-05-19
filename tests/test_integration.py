"""
Integration tests for the Activity Bus.
"""
import pytest

from activity_bus import ActivityBus, when
from activity_bus.registry import registry


# Clear registry before each test
@pytest.fixture(autouse=True)
def clear_registry():
    registry.clear()
    yield


@pytest.mark.asyncio
async def test_submit_and_process():
    """Test the end-to-end flow of submitting and processing an activity."""
    # Create an ActivityBus instance with default in-memory store
    bus = ActivityBus()

    # Register a test behavior
    @when({"type": "Create", "object": {"type": "Note"}})
    def test_behavior(activity):
        activity["result"].append({
            "type": "Log",
            "content": f"Processed note with content: {activity['object']['content']}"
        })

        # Return a new activity to be submitted
        return [{
            "type": "Announce",
            "actor": activity["actor"],
            "object": activity["id"],
            "summary": "Announcing a new note"
        }]

    # Create a test activity
    activity = {
        "type": "Create",
        "actor": "https://example.com/users/123",
        "object": {
            "type": "Note",
            "content": "This is a test note"
        }
    }

    # Submit the activity
    submitted = await bus.submit(activity)

    # Process the next activity
    processed = await bus.process_next()

    # Verify the activity was processed correctly
    assert processed["type"] == submitted["type"]
    assert processed["id"] == submitted["id"]
    assert processed["actor"] == submitted["actor"]

    # Verify the behavior was executed
    assert len(processed["result"]) == 1
    assert processed["result"][0]["type"] == "Log"
    assert "Processed note with content" in processed["result"][0]["content"]

    # Verify that a new Announce activity was submitted and is in the queue
    assert bus.queue.qsize() == 1

    # Process the new activity
    announce = await bus.process_next()

    # Verify the announce activity
    assert announce["type"] == "Announce"
    assert announce["actor"] == "https://example.com/users/123"
    assert announce["object"] == submitted["id"]
    assert announce["summary"] == "Announcing a new note"
    assert "context" in announce
    assert announce["context"] == submitted["id"]

    # Queue should be empty now
    assert bus.queue.qsize() == 0


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling during activity processing."""
    # Create an ActivityBus instance
    bus = ActivityBus()

    # Register a behavior that throws an exception
    @when({"type": "Create", "object": {"type": "Note"}})
    def error_behavior(activity):
        raise ValueError("Test error")

    # Create a test activity
    activity = {
        "type": "Create",
        "actor": "https://example.com/users/123",
        "object": {
            "type": "Note",
            "content": "This is a test note"
        }
    }

    # Submit the activity
    submitted = await bus.submit(activity)

    # Process the next activity - should convert to tombstone
    tombstone = await bus.process_next()

    # Verify the activity was tombstoned
    assert tombstone["type"] == "Tombstone"
    assert tombstone["formerType"] == "Create"
    assert tombstone["id"] == submitted["id"]

    # Queue should be empty
    assert bus.queue.qsize() == 0

    # Try to dereference the activity from the store
    stored = await bus.store.dereference(submitted["id"])

    # Should return the tombstone
    assert stored["type"] == "Tombstone"
