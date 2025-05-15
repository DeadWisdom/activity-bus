# Activity Bus Specification

## Overview

Activity Bus is a Python library for processing Activity Streams 2.0 activities via a rule-based engine. It is designed to work in concert with [Activity Store](https://github.com/DeadWisdom/activity-store) and provides a high-level pipeline for submitting, validating, storing, and processing activities using dynamic, declarative rules and effects.

## Design Goals

- Build on Activity Store for storage, caching, and dereferencing
- Easy creation and management of rules and effects
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
2. Fetch all rules from `/sys/rules`
3. Match each rule using `frame(activity, rule["match"], require_match=True)`
4. Execute effects from matched rules (sorted by priority)
5. If `activity["result"]` includes new activities, submit each with `context = activity["id"]`
6. On any exception:

   - Append an ephemeral `{"type": "Error", "content": "<stacktrace>", "context": activity["id"]}` to `activity["result"]`
   - Convert activity to `{"type": "Tombstone", "formerType": ..., "deleted": <now>}`
   - Store updated activity

## Effects

```python
@effect(priority=100)
def log_to_console(activity):
    print(activity)
```

- Registered using `@effect`
- ID is inferred from `module.function`
- Registered eagerly on import
- Automatically stored in `/sys/effects`
- Referenced by `id` in Rule definitions

## Rules

- Stored in `/sys/rules`
- Defined as YAML:

```yaml
id: rule.log_create
match:
  type: Create
effect:
  - myapp.effects.log_to_console
priority: 100
type: Rule
```

- Loaded via `await bus.load_rules("rules/")`
- Editable at runtime; dynamically fetched before every match

## ActivityBus API

```python
class ActivityBus:
    async def submit(self, activity: dict) -> dict
    async def process(self, activity: dict) -> dict
    async def process_next(self) -> None
    async def load_effects(self, *modules: str) -> list[dict]
    async def load_rules(self, *folders: str) -> list[dict]

    self.queue: asyncio.Queue
    self.store: ActivityStore
    self.namespace: str
```

## Error Handling

- Base: `ActivityBusError`
- Subclasses: `InvalidActivityError`, `EffectExecutionError`, `ActivityIdError`, etc.
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
- Defined as a pluggable Effect (e.g., `deliver_to_targets(activity)`)
