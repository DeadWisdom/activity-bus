# Activity Bus Implementation Plan

This document provides a step-by-step implementation guide to bring the Activity Bus to life. Each step is focused, incremental, and testable.
MANDAMUS TIBI write tests before implementing any feature, even if that's not explicitly stated in the steps.

## 1. Project Setup - COMPLETED

1.1 Create a Python package `activity_bus`
1.2 Set up dependencies: `activity_store` (via https://github.com/DeadWisdom/activity-store), `pyyaml`, `nanoid`, `asyncio`
1.3 Create base directory structure:

```
activity_bus/
  __init__.py
  bus.py
  effects.py
  rules.py
  registry.py
  errors.py
```

## 2. Core Class: `ActivityBus` - COMPLETED

2.1 Implement `ActivityBus.__init__(store=None, namespace=None)`
2.2 Instantiate `asyncio.Queue`, set default `ActivityStore` if not provided

## 3. Validation & Submission - COMPLETED

3.1 Add `async def submit(self, activity: dict)`
3.2 Implement:

- Actor check
- ID check/generation using nanoid
- Scope validation
- Timestamping
- Store using `ActivityStore`
- Enqueue

## 4. Worker Functions - COMPLETED

4.1 Add `async def process_next(self)`
4.2 Add `async def process(self, activity)`
4.3 Load rules, match using `frame()`, execute effects
4.4 Append to `activity['result']` as needed
4.5 Handle errors: tombstone + error object
4.6 Store mutated activity

## 5. Rules - COMPLETED

5.1 Create `rules.py` with `load_rules(*folders)`
5.2 Parse YAMLs and validate structure
5.3 Store each rule in `/sys/rules`

## 6. Effects - COMPLETED

6.1 Create `effects.py` with `@effect` decorator
6.2 Register effect into global registry
6.3 Store metadata to `/sys/effects`
6.4 Add `load_effects(*modules)` for scanning modules

## 7. Errors - COMPLETED

7.1 Define `ActivityBusError`
7.2 Add `InvalidActivityError`, `EffectExecutionError`, `ActivityIdError`, etc.
7.3 Use in `submit()` and `process()`

## 8. Integration with ActivityStore - COMPLETED

8.1 Use `store.store()`, `store.dereference()`, `store.convert_to_tombstone()`
8.2 Leverage store's querying and caching

## 9. Review Tests - COMPLETED

9.1 Ensure unit tests are available for:

- Activity validation
- ID generation
- Rule matching
- Effect execution
- Error handling
  9.2 Integration tests for end-to-end `submit()` + `process_next()`

## 10. Example & Usage - COMPLETED

10.1 Create `examples/` folder
10.2 Include sample rules, effects, and activities
10.3 Demonstrate running the processor in a loop

## 11. Optional Next Steps - FOR FUTURE WORK

11.1 Add command line dev runner
11.2 Add dev server to inspect state via web UI
11.3 Explore caching matched rules
11.4 Add support for metrics and logging observers