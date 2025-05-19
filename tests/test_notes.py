"""
Tests for the standard notes behaviors.
"""

import pytest

from activity_bus.errors import InvalidActivityError
from activity_bus.standard.notes import create_note, create_reply, delete_note, update_note


def test_create_note():
    """Test the create_note behavior."""
    # Create a valid activity
    activity = {
        "type": "Create",
        "actor": "https://example.com/users/123",
        "object": {"type": "Note", "content": "This is a test note"},
        "result": [],
    }

    # Execute the behavior
    result = create_note(activity)

    # Verify no new activities are returned
    assert result is None

    # Verify a log entry was added to the result
    assert len(activity["result"]) == 1
    assert activity["result"][0]["type"] == "Log"
    assert "Created note with content" in activity["result"][0]["content"]


def test_create_note_invalid():
    """Test the create_note behavior with an invalid note (missing content)."""
    # Create an invalid activity (note missing content)
    activity = {"type": "Create", "actor": "https://example.com/users/123", "object": {"type": "Note"}, "result": []}

    # Execute the behavior - should raise InvalidActivityError
    with pytest.raises(InvalidActivityError) as excinfo:
        create_note(activity)

    # Verify the error message
    assert "Note must have a content field" in str(excinfo.value)

    # Verify no log entry was added
    assert len(activity["result"]) == 0


def test_update_note():
    """Test the update_note behavior."""
    # Create a valid activity
    activity = {
        "type": "Update",
        "actor": "https://example.com/users/123",
        "object": {"type": "Note", "id": "https://example.com/notes/456", "content": "This is an updated test note"},
        "result": [],
    }

    # Execute the behavior
    result = update_note(activity)

    # Verify no new activities are returned
    assert result is None

    # Verify a log entry was added to the result
    assert len(activity["result"]) == 1
    assert activity["result"][0]["type"] == "Log"
    assert "Updated note" in activity["result"][0]["content"]


def test_update_note_invalid_no_id():
    """Test the update_note behavior with a note missing an ID."""
    # Create an invalid activity (note missing ID)
    activity = {
        "type": "Update",
        "actor": "https://example.com/users/123",
        "object": {"type": "Note", "content": "This is an updated test note"},
        "result": [],
    }

    # Execute the behavior - should raise InvalidActivityError
    with pytest.raises(InvalidActivityError) as excinfo:
        update_note(activity)

    # Verify the error message
    assert "Note being updated must have an ID" in str(excinfo.value)

    # Verify no log entry was added
    assert len(activity["result"]) == 0


def test_update_note_invalid_no_content():
    """Test the update_note behavior with a note missing content."""
    # Create an invalid activity (note missing content)
    activity = {
        "type": "Update",
        "actor": "https://example.com/users/123",
        "object": {
            "type": "Note",
            "id": "https://example.com/notes/456",
        },
        "result": [],
    }

    # Execute the behavior - should raise InvalidActivityError
    with pytest.raises(InvalidActivityError) as excinfo:
        update_note(activity)

    # Verify the error message
    assert "Updated note must have a content field" in str(excinfo.value)

    # Verify no log entry was added
    assert len(activity["result"]) == 0


def test_delete_note():
    """Test the delete_note behavior."""
    # Create a valid activity
    activity = {
        "type": "Delete",
        "actor": "https://example.com/users/123",
        "object": {"type": "Note", "id": "https://example.com/notes/456"},
        "result": [],
    }

    # Execute the behavior
    result = delete_note(activity)

    # Verify no new activities are returned
    assert result is None

    # Verify a log entry was added to the result
    assert len(activity["result"]) == 1
    assert activity["result"][0]["type"] == "Log"
    assert "Deleted note" in activity["result"][0]["content"]


def test_delete_note_invalid():
    """Test the delete_note behavior with an invalid note (missing ID)."""
    # Create an invalid activity (note missing ID)
    activity = {"type": "Delete", "actor": "https://example.com/users/123", "object": {"type": "Note"}, "result": []}

    # Execute the behavior - should raise InvalidActivityError
    with pytest.raises(InvalidActivityError) as excinfo:
        delete_note(activity)

    # Verify the error message
    assert "Note being deleted must have an ID" in str(excinfo.value)

    # Verify no log entry was added
    assert len(activity["result"]) == 0


def test_create_reply():
    """Test the create_reply behavior."""
    # Create a valid activity
    activity = {
        "type": "Create",
        "actor": "https://example.com/users/123",
        "object": {"type": "Note", "content": "This is a reply", "inReplyTo": "https://example.com/notes/789"},
        "result": [],
    }

    # Execute the behavior
    result = create_reply(activity)

    # Verify a notification activity is returned
    assert result is not None
    assert len(result) == 1
    assert result[0]["type"] == "Notification"
    assert result[0]["summary"] == "New reply to your note"
    assert result[0]["actor"] == activity["actor"]
    assert result[0]["object"] == activity
    assert result[0]["target"] == "https://example.com/notes/789"

    # Verify a log entry was added to the result
    assert len(activity["result"]) == 1
    assert activity["result"][0]["type"] == "Log"
    assert "Created reply to" in activity["result"][0]["content"]


def test_create_reply_with_object_in_reply_to():
    """Test the create_reply behavior with an object as inReplyTo."""
    # Create a valid activity with an object for inReplyTo
    activity = {
        "type": "Create",
        "actor": "https://example.com/users/123",
        "object": {
            "type": "Note",
            "content": "This is a reply",
            "inReplyTo": {"id": "https://example.com/notes/789", "type": "Note"},
        },
        "result": [],
    }

    # Execute the behavior
    result = create_reply(activity)

    # Verify a notification activity is returned
    assert result is not None
    assert len(result) == 1
    assert result[0]["type"] == "Notification"
    assert result[0]["target"] == "https://example.com/notes/789"

    # Verify a log entry was added to the result
    assert len(activity["result"]) == 1
    assert activity["result"][0]["type"] == "Log"
    assert "Created reply to" in activity["result"][0]["content"]


def test_create_reply_invalid_no_in_reply_to():
    """Test the create_reply behavior with a missing inReplyTo field."""
    # Create an invalid activity (missing inReplyTo)
    activity = {
        "type": "Create",
        "actor": "https://example.com/users/123",
        "object": {"type": "Note", "content": "This is a reply", "inReplyTo": None},
        "result": [],
    }

    # Execute the behavior - should raise InvalidActivityError
    with pytest.raises(InvalidActivityError) as excinfo:
        create_reply(activity)

    # Verify the error message
    assert "Reply must have a valid inReplyTo field" in str(excinfo.value)

    # Verify no log entry was added
    assert len(activity["result"]) == 0


def test_create_reply_invalid_no_content():
    """Test the create_reply behavior with a missing content field."""
    # Create an invalid activity (missing content)
    activity = {
        "type": "Create",
        "actor": "https://example.com/users/123",
        "object": {"type": "Note", "inReplyTo": "https://example.com/notes/789"},
        "result": [],
    }

    # Execute the behavior - should raise InvalidActivityError
    with pytest.raises(InvalidActivityError) as excinfo:
        create_reply(activity)

    # Verify the error message
    assert "Reply note must have a content field" in str(excinfo.value)

    # Verify no log entry was added
    assert len(activity["result"]) == 0
