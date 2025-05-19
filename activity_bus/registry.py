"""
This module provides functionality for registering and retrieving behaviors.
"""

from collections.abc import Callable


class BehaviorRegistry:
    """Registry for storing and retrieving behavior functions."""

    def __init__(self):
        """Initialize an empty behavior registry."""
        self._behaviors: dict[str, Callable] = {}

    def register(self, behavior_id: str, function: Callable) -> None:
        """
        Register a behavior function with a specific ID.

        Args:
            behavior_id: The ID of the behavior, typically in the form of "/sys/behaviors/{module}.{function}"
            function: The callable function to be executed when the behavior is matched
        """
        self._behaviors[behavior_id] = function

    def get(self, behavior_id: str) -> Callable | None:
        """
        Get a behavior function by its ID.

        Args:
            behavior_id: The ID of the behavior to retrieve

        Returns:
            The behavior function if found, None otherwise
        """
        return self._behaviors.get(behavior_id)

    def clear(self) -> None:
        """Clear all registered behaviors."""
        self._behaviors.clear()

    def all_behaviors(self) -> dict[str, Callable]:
        """
        Return all registered behaviors.

        Returns:
            Dictionary mapping behavior IDs to their functions
        """
        return dict(self._behaviors)


# Global registry instance
registry = BehaviorRegistry()
