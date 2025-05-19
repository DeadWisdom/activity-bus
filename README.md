# Activity Bus

A Python library for processing Activity Streams 2.0 activities via a rule-based engine. Activity Bus is designed to work in concert with [Activity Store](https://github.com/DeadWisdom/activity-store) and provides a high-level pipeline for submitting, validating, storing, and processing activities using dynamic, declarative behaviors.

## Installation

```bash
pip install activity-bus
```

## Features

- Build on Activity Store for storage, caching, and dereferencing
- Easy creation and management of behaviors
- Clean, async-first interface
- Compatible with ActivityPub delivery semantics
- Agent-friendly, auditable, and introspectable
- Support for asynchronous and dynamic rule processing

## Basic Usage

```python
import asyncio
from activity_bus import ActivityBus, when

# Define a behavior
@when({"type": "Create", "object": {"type": "Note"}})
def create_note(activity):
    print(f"Note created with content: {activity['object']['content']}")
    # You can return new activities to be submitted
    return [{
        "type": "Notification",
        "summary": "New note created",
        "actor": activity["actor"]
    }]

async def main():
    # Create a new ActivityBus instance
    bus = ActivityBus()
    
    # Submit an activity
    activity = {
        "type": "Create",
        "actor": "https://example.com/users/user1",
        "object": {
            "type": "Note",
            "content": "Hello, world!"
        }
    }
    
    await bus.submit(activity)
    
    # Process the next activity in the queue
    processed = await bus.process_next()
    
    # Process any new activities that were created
    notification = await bus.process_next()
    
    print(f"Processed: {processed}")
    print(f"Notification: {notification}")

# Run the example
asyncio.run(main())
```

## Core Concepts

### Activities

- Must contain at minimum: `actor`, `type`, and optionally `id`
- If `id` is not present, it is generated: `/users/<user-id>/outbox/<nanoid>`
- Must be scoped under actor's URI; otherwise, rejected
- On submission, `published` timestamp is set

### Submit Workflow

```python
await bus.submit(activity)
```

1. Validate required fields
2. Set ID if missing
3. Validate ID scope
4. Store activity in ActivityStore
5. Enqueue activity in in-memory asyncio.Queue

### Process Workflow

```python
await bus.process_next()
```

1. Dequeue activity
2. Fetch all behaviors from `/sys/behaviors`
3. Match each behavior using `frame(activity, behavior["when"], require_match=True)`
4. Execute function for each matching behavior
5. If `activity["result"]` includes new activities, submit each with `context = activity["id"]`
6. On any exception:
   - Append an error to `activity["result"]`
   - Convert activity to a Tombstone
   - Store updated activity

## Documentation

For more detailed documentation, see the comments in the source code and the `SPEC.md` file.

## Development

### Running Tests

```bash
# Install test dependencies
pip install -e ".[test]"

# Run all tests
pytest

# Run with coverage
pytest --cov=activity_bus
```

## License

MIT