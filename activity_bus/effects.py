# Implements the effect decorator and loading functionality
# Manages registration and execution of effect functions

import importlib

from .errors import EffectLoadError
from .registry import registry


def effect(priority=100, **metadata):
    """
    Decorator for registering effect functions.

    Args:
        priority (int): Execution priority (lower numbers execute first)
        **metadata: Additional metadata to store with the effect

    Returns:
        callable: Decorated function
    """

    def decorator(func):
        module_name = func.__module__
        function_name = func.__name__
        effect_id = f"{module_name}.{function_name}"

        # Store the original function, not the wrapper
        registered_func = func

        registry.register(effect_id=effect_id, func=registered_func, priority=priority, **metadata)

        # Return original function, not a wrapper to preserve identity
        return func

    return decorator


async def load_effects(*modules):
    """
    Import modules to load their effects.

    Args:
        *modules (str): Module names to import

    Returns:
        list: List of registered effects

    Raises:
        EffectLoadError: If a module couldn't be imported
    """
    results = []

    for module_name in modules:
        try:
            importlib.import_module(module_name)

            # Find all effects registered from this module
            for effect_id, effect_data in registry.effects.items():
                if effect_id.startswith(f"{module_name}."):
                    results.append(effect_data)

        except ImportError as e:
            raise EffectLoadError(f"Failed to import module '{module_name}': {e!s}") from e

    return registry.list_effects()
