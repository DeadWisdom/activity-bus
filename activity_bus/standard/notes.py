"""
This module contains behaviors for working with Note objects in Activity Streams.
"""
from typing import Any

from ..behaviors import when
from ..errors import InvalidActivityError


@when({"type": "Create", "object": {"type": "Note"}})
def create_note(activity: dict[str, Any]) -> list[dict[str, Any]] | None:
    """
    Behavior for handling the creation of a Note.
    
    Args:
        activity: The Create activity with a Note object
        
    Returns:
        None or list of new activities to submit
    """
    note = activity.get("object", {})

    # Ensure the note has required fields
    if "content" not in note:
        raise InvalidActivityError("Note must have a content field")

    # If successful, add a log entry to the result
    activity["result"].append({
        "type": "Log",
        "content": f"Created note with content: {note.get('content')[:50]}..."
    })

    return None


@when({"type": "Update", "object": {"type": "Note"}})
def update_note(activity: dict[str, Any]) -> list[dict[str, Any]] | None:
    """
    Behavior for handling the update of a Note.
    
    Args:
        activity: The Update activity with a Note object
        
    Returns:
        None or list of new activities to submit
    """
    note = activity.get("object", {})

    # Ensure the note has required fields
    if "id" not in note:
        raise InvalidActivityError("Note being updated must have an ID")

    if "content" not in note:
        raise InvalidActivityError("Updated note must have a content field")

    # Log the update
    activity["result"].append({
        "type": "Log",
        "content": f"Updated note {note.get('id')} with content: {note.get('content')[:50]}..."
    })

    return None


@when({"type": "Delete", "object": {"type": "Note"}})
def delete_note(activity: dict[str, Any]) -> list[dict[str, Any]] | None:
    """
    Behavior for handling the deletion of a Note.
    
    Args:
        activity: The Delete activity with a Note object
        
    Returns:
        None or list of new activities to submit
    """
    note = activity.get("object", {})

    # Ensure the note has required fields
    if "id" not in note:
        raise InvalidActivityError("Note being deleted must have an ID")

    # Log the deletion
    activity["result"].append({
        "type": "Log",
        "content": f"Deleted note {note.get('id')}"
    })

    return None


@when({"type": "Create", "object": {"type": "Note", "inReplyTo": {"@exists": True}}})
def create_reply(activity: dict[str, Any]) -> list[dict[str, Any]] | None:
    """
    Behavior for handling the creation of a Note that is a reply to another object.
    
    Args:
        activity: The Create activity with a Note object that has inReplyTo
        
    Returns:
        None or list of new activities to submit
    """
    note = activity.get("object", {})
    in_reply_to = note.get("inReplyTo")

    # Validate the in_reply_to field
    if not in_reply_to:
        raise InvalidActivityError("Reply must have a valid inReplyTo field")

    # If in_reply_to is a string (ID), convert to dict format for consistency
    if isinstance(in_reply_to, str):
        in_reply_to = {"id": in_reply_to}

    # Ensure the note has content
    if "content" not in note:
        raise InvalidActivityError("Reply note must have a content field")

    # Log the reply creation
    activity["result"].append({
        "type": "Log",
        "content": f"Created reply to {in_reply_to.get('id')} with content: {note.get('content')[:50]}..."
    })

    # Return a Notification activity to notify the original note's author
    return [{
        "type": "Notification",
        "summary": "New reply to your note",
        "actor": activity.get("actor"),
        "object": activity,
        "target": in_reply_to.get("id")
    }]
