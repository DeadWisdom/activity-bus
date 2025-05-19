# Activity Bus Implementation Plan

This document provides a step-by-step implementation guide to bring the Activity Bus to life. Each step is focused, incremental, and testable.

## MANDAMUS TIBI

- Alsways write tests before implementing features, even if that's not explicitly stated in the steps.
- However, do not write tests for trivialities like the presence of a class or that exceptions can be raised.
- Completed steps shall be marked with ✅

## 1. Project Setup

- Create a Python package `activity_bus`
- Set up dependencies: `activity_store` (via https://github.com/DeadWisdom/activity-store), `pyyaml`, `nanoid`, `asyncio`, `pytest`
- Create base directory structure:

```
activity_bus/
  __init__.py
  bus.py
  behaviors.py
  registry.py
  errors.py
  standard/
    notes.py
```

## 2. Core Class: `ActivityBus`

- Implement `ActivityBus.__init__(store=None)`
- Instantiate `asyncio.Queue`, set default `ActivityStore` if not provided

## 3. Validation & Submission

- Add `async def submit(self, activity: dict)`
- Implement:
  - Actor check
  - ID check/generation using nanoid
  - Scope validation
  - Timestamping
  - Store using `ActivityStore`
  - Enqueue

## 4. Behaviors

- Create `behaviors.py` with `@when` decorator
- Register behavior in registry
- Store each behavior in `/sys/behaviors`
- Create standard/notes.py that has behaviours for basic management of Notes (like tweets) and replying

## 5. Worker Functions

- Add `async def process_next(self)`
- Add `async def process(self, activity)`
- Load behaviors, match using `frame()`, execute functions
- Append to `activity['result']` as needed
- Handle errors: tombstone + error object
- Store mutated activity

## 7. Errors

- Define `ActivityBusError`
- Add `InvalidActivityError`, `BehaviorExecutionError`, `ActivityIdError`, etc.
- Use in `submit()` and `process()`

## 8. Integration with ActivityStore

- Use `store.store()`, `store.dereference()`, `store.convert_to_tombstone()`
- Leverage store's querying and caching

## 9. Review Tests

- Ensure unit tests are available for:

- Activity validation
- ID generation
- Behavior matching and execution
- Standard notes behaviors
- Error handling
- Integration tests for end-to-end `submit()` + `process_next()`
