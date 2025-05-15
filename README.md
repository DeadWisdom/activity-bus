# Activity Bus

A Python library for processing Activity Streams 2.0 activities via a rule-based engine. Activity Bus works in concert with [Activity Store](https://github.com/DeadWisdom/activity-store) to provide a high-level pipeline for submitting, validating, storing, and processing activities using dynamic, declarative rules and effects.

## Installation

```bash
# Install from PyPI
pip install activity-bus

# Install from source
git clone https://github.com/DeadWisdom/activity-bus.git
cd activity-bus
pip install -e .
```

## Requirements

- Python 3.8+
- [Activity Store](https://github.com/DeadWisdom/activity-store)
- PyYAML
- nanoid
- asyncio

## Basic Usage

```python
import asyncio
from activity_bus import ActivityBus, effect

# Define an effect
@effect(priority=100)
def log_to_console(activity):
    print(f"Processing activity: {activity['type']}")
    return {"type": "Log", "content": "Activity logged"}

async def main():
    # Initialize ActivityBus
    bus = ActivityBus(namespace="https://example.com")
    
    # Load effects from the current module
    await bus.load_effects("__main__")
    
    # Load rules from a directory
    await bus.load_rules("rules/")
    
    # Submit an activity
    activity = {
        "type": "Create",
        "actor": "user1",
        "object": {
            "type": "Note",
            "content": "Hello, world!"
        }
    }
    
    submitted = await bus.submit(activity)
    print(f"Submitted activity with ID: {submitted['id']}")
    
    # Process the activity
    processed = await bus.process_next()
    print(f"Processed activity results: {processed.get('result')}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Rules

Rules are defined in YAML files and stored in the Activity Store. Example rule:

```yaml
id: rule.log_create
match:
  type: Create
effect:
  - myapp.effects.log_to_console
priority: 100
type: Rule
```

Rules are loaded using:

```python
await bus.load_rules("path/to/rules/")
```

## Effects

Effects are Python functions registered with the `@effect` decorator:

```python
from activity_bus import effect

@effect(priority=100)
def log_to_console(activity):
    print(activity)
    return {"type": "Log", "content": "Activity logged"}
```

Effects are loaded using:

```python
await bus.load_effects("my_module.effects")
```

## Processing

Activities are processed using rules and effects:

1. Activities are submitted via `await bus.submit(activity)`
2. Activities are processed via `await bus.process_next()`
3. Matching rules are found and their effects are executed
4. Results are stored in the activity's `result` field
5. Processed activities are stored back in the Activity Store

## Examples

Run the included example to see Activity Bus in action:

```bash
python -m activity_bus --example
```

For more examples, check the `examples/` directory.

## Documentation

For detailed documentation, see the [Specification](SPEC.md) and implementation in the `activity_bus/` directory.

## License

This project is licensed under the MIT License.