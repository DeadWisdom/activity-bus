# Activity Bus Specification

## Overview

Activity Bus is a Python library for processing Activity Streams 2.0 activities via a rule-based engine. It is designed to work in concert with [Activity Store](https://github.com/DeadWisdom/activity-store) and provides a high-level pipeline for submitting, validating, storing, and processing activities using dynamic, declarative behaviors.

## Design Goals

- Build on Activity Store for storage, caching, and dereferencing
- Easy creation and management of behaviors
- Clean, async-first interface
- Compatible with ActivityPub delivery semantics
- Agent-friendly, auditable, and introspectable
- Support for asynchronous and dynamic rule processing

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
4. Execute builtin for each matching behavior
5. If `activity["result"]` includes new activities, submit each with `context = activity["id"]`
6. On any exception:

   - Append an ephemeral `{"type": "Error", "content": "<stacktrace>", "context": activity["id"]}` to `activity["result"]`
   - Convert activity to `{"type": "Tombstone", "formerType": ..., "deleted": <now>}`
   - Store updated activity

## Behaviors

```python
# notes.py

@when({"type": "Create", "object": {"type": "Note"}})
def create_note(activity):
    ...
```

Creates

```json
{
  "id": "/sys/behaviors/notes.create_note",
  "type": "Behavior",
  "when": { "type": "Create", "object": { "type": "Note" } }
}
```

- Registered using `@when` into a dict of {ID: function}
- Added to `/sys/behaviors`
- ID is inferred from `module.function` or can be set as keyword in e.g. `@when(id=whatever)`

## ActivityBus API

```python
class ActivityBus:
    async def submit(self, activity: dict) -> dict
    async def process(self, activity: dict) -> dict
    async def process_next(self) -> None

    self.queue: asyncio.Queue
    self.store: ActivityStore
    self.namespace: str
```

## Error Handling

- Base: `ActivityBusError`
- Subclasses: `InvalidActivityError`, `BehaviorExecutionError`, `ActivityIdError`, etc.
- During `process()`, **all exceptions**:

  - Added to `activity["result"]` as transient `Error` objects
  - Activity converted to Tombstone
  - Only the Tombstone is stored

## Activity Store Integration

- Default to `ActivityStore()` unless custom one is provided
- Used for:

  - Storing and retrieving activities
  - Tombstoning
  - Dereferencing objects
  - Normalization, querying, and caching

## Result Field

- `activity["result"]` is an open container

  - Can include logs, errors, metrics, new activities, etc.

- Updated in-place during processing
- Not formally structured

## Delivery

- No built-in delivery logic
- Defined as a pluggable Behavior (e.g., `deliver_to_targets(activity)`)

---

The following is the Activity Store library, which you will be using.

# Activity Store

Activity Store is an async-first Python library for securely storing and retrieving [Activity Streams](https://www.w3.org/ns/activitystreams) JSON-LD objects and collections. It provides a flexible backend and caching abstraction layer with support for dereferencing, normalization, and querying, while adhering to JSON-LD and Activity Streams conventions.

## Features

- Async-first API with synchronous wrapper
- Pluggable storage backends
  - In-memory backend for testing
  - Elasticsearch backend for production
  - Redis cache backend for improved performance
- Dereferencing with TTL-based caching
- Collection management
- Structured querying
- Tombstone support for deleted objects
- Context-managed usage pattern
- Structured logging with metadata support

## Installation

```bash
# Basic installation
pip install activity-store

# With Elasticsearch backend
pip install activity-store[es]

# With Redis cache
pip install activity-store[redis]

# With all backends
pip install activity-store[es,redis]
```

## Basic Usage

```python
import asyncio
from activity_store import ActivityStore

async def main():
    # Context-managed usage
    async with ActivityStore() as store:
        # Store an object
        object_id = await store.store({
            "id": "https://example.com/objects/123",
            "type": "Note",
            "content": "Hello, world!",
            "published": "2023-01-01T00:00:00Z"
        })

        # Retrieve the object
        note = await store.dereference(object_id)

        # Add to a collection
        await store.add_to_collection(note, "notes")

        # Query for objects with direct keyword arguments
        results = await store.query(
            collection="notes",
            type="Note",
            size=10
        )

        # Convert to tombstone when deleting
        tombstone = await store.convert_to_tombstone(note)

# Run the example
asyncio.run(main())
```

## Using with Elasticsearch

```python
import asyncio
from activity_store import ActivityStore

async def main():
    # Create an Elasticsearch backend
    backend = ElasticsearchBackend(
        es_url="http://localhost:9200",
        index_prefix="activity_store"
    )

    # Use with a cloud service
    # backend = ElasticsearchBackend(
    #     client=AsyncElasticsearch(
    #         cloud_id="your-cloud-id",
    #         api_key="your-api-key"
    #     ),
    #     index_prefix="activity_store"
    # )

    # Context-managed usage with custom backend
    async with ActivityStore(backend=backend) as store:
        # Use the store as before
        object_id = await store.store({
            "id": "https://example.com/objects/123",
            "type": "Note",
            "content": "Hello, world!",
            "published": "2023-01-01T00:00:00Z"
        })

        # Query with Elasticsearch's full-text search capabilities
        results = await store.query(
            text="hello world",
            sort="published:desc"
        )

asyncio.run(main())
```

## Using with Redis Cache

```python
import asyncio
from activity_store import ActivityStore
from activity_store.backends.elastic import ElasticsearchBackend
from activity_store.cache.redis import RedisCacheBackend

async def main():
    # Create the storage backend
    storage = ElasticsearchBackend(
        es_url="http://localhost:9200",
        index_prefix="activity_store"
    )

    # Create the cache backend
    cache = RedisCacheBackend(
        redis_url="redis://localhost:6379/0",
        namespace="activity_store"
    )

    # Create a store with both backends
    async with ActivityStore(backend=storage, cache=cache) as store:
        # Now use the store as before
        object_id = await store.store({
            "id": "https://example.com/objects/123",
            "type": "Note",
            "content": "Hello, world!",
            "published": "2023-01-01T00:00:00Z"
        })

        # First call will fetch from Elasticsearch and cache in Redis
        note1 = await store.dereference(object_id)

        # Second call will use the Redis cache
        note2 = await store.dereference(object_id)

asyncio.run(main())
```

## Synchronous Usage

```python
from activity_store import SyncActivityStore

# Context-managed usage
with SyncActivityStore() as store:
    # Same methods as async API but synchronous
    object_id = store.store({
        "id": "https://example.com/objects/123",
        "type": "Note",
        "content": "Hello, world!"
    })

    note = store.dereference(object_id)
    store.add_to_collection(note, "notes")
```

## Advanced Querying

```python
import asyncio
from activity_store import ActivityStore
from activity_store.query import Query

async def main():
    async with ActivityStore() as store:
        # Add some objects
        for i in range(10):
            await store.store({
                "id": f"https://example.com/notes/{i}",
                "type": "Note",
                "content": f"Note {i}",
                "published": f"2023-01-{i+1:02d}T00:00:00Z",
                "tag": ["test", f"tag{i % 3}"]
            })

        # Query by text content
        results = await store.query(text="Note 5")

        # Query by type
        results = await store.query(type="Note")

        # Query by keywords/tags
        results = await store.query(keywords=["tag1"])

        # Query with sorting
        results = await store.query(sort="published:desc")

        # Query with pagination
        results = await store.query(size=5)

        # Query with multiple parameters
        results = await store.query(
            type="Note",
            keywords=["tag1"],
            sort="published:desc",
            size=5
        )

        # Using the Query object directly (for more complex scenarios)
        from activity_store.query import Query
        results = await store.query(Query(
            collection="notes",
            type="Note",
            keywords=["tag1", "tag2"],
            sort="published:desc",
            size=5
        ))

asyncio.run(main())
```

## Configuration

The library respects the following environment variables:

- `ACTIVITY_STORE_BACKEND`: Backend type to use (default: "memory")
- `ACTIVITY_STORE_CACHE`: Cache type to use (default: "memory")
- `ACTIVITY_STORE_NAMESPACE`: Namespace for this store (default: "activity_store")
- `ELASTICSEARCH_CLOUD_ID`: Cloud ID for Elasticsearch cloud service
- `ELASTICSEARCH_PASSWORD`: API key or password for Elasticsearch
- `ELASTICSEARCH_NAMESPACE`: Namespace for Elasticsearch indices

## Documentation

For more detailed documentation, see the comments in the source code and the `SPEC.md` file.

## Development

### Running Tests

```bash
# Install test dependencies
pip install activity-store[test]

# Run all tests
pytest

# Run with coverage
pytest --cov=activity_store

# Run integration tests
pytest tests/integration/
```

### Integration Tests

For Elasticsearch integration tests:

- Ensure an Elasticsearch server is running at http://localhost:9200
- Or set the `ES_URL` environment variable to point to your Elasticsearch server
- Or set the `ELASTICSEARCH_CLOUD_ID` and `ELASTICSEARCH_PASSWORD` for using Elastic Cloud

For Redis integration tests:

- Ensure a Redis server is running at redis://localhost:6379/0
- Or set the `REDIS_URL` environment variable to point to your Redis server
