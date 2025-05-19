"""
This module provides decorators for defining and registering activity behaviors.
"""
import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any

from .registry import registry


def when(pattern: dict[str, Any], *, id: str | None = None):
    """
    Decorator for registering behavior functions that should be triggered when an activity
    matches the specified pattern.
    
    Args:
        pattern: A dictionary pattern to match against activities using ActivityStore's frame function
        id: Optional custom ID for the behavior, if not provided it will be generated from the module and function name
    
    Returns:
        Decorator function that registers the behavior
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # Generate ID from module and function name if not provided
        behavior_id = id
        if behavior_id is None:
            module = inspect.getmodule(func)
            module_name = module.__name__.split('.')[-1] if module else "__main__"
            behavior_id = f"/sys/behaviors/{module_name}.{func.__name__}"

        # Store the pattern on the function for later use
        wrapper._when_pattern = pattern
        wrapper._behavior_id = behavior_id

        # Register the behavior
        registry.register(behavior_id, wrapper)

        return wrapper

    return decorator


def get_all_behaviors() -> dict[str, dict[str, str | dict[str, Any] | Callable]]:
    """
    Get all registered behaviors with their patterns.
    
    Returns:
        Dictionary of behavior objects with IDs as keys
    """
    all_behaviors = {}
    for behavior_id, func in registry.all_behaviors().items():
        if hasattr(func, '_when_pattern'):
            all_behaviors[behavior_id] = {
                "id": behavior_id,
                "type": "Behavior",
                "when": func._when_pattern,
                "_function": func  # Internal use only
            }

    return all_behaviors
