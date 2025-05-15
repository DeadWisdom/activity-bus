# Implements the core ActivityBus class for activity processing
# Provides validation, submission, and processing functionalities

import asyncio
import inspect
import traceback
from datetime import UTC, datetime

from nanoid import generate as nanoid_generate

from .effects import load_effects
from .errors import (
    ActivityBusError,
    ActivityIdError,
    InvalidActivityError,
)
from .registry import registry
from .rules import load_rules

try:
    # Try to import activity_store if available
    from activity_store import ActivityStore, frame
except ImportError:
    ActivityStore = None
    frame = None


class ActivityBus:
    """
    Core class for processing Activity Streams 2.0 activities via rules and effects.

    Attributes:
        queue (asyncio.Queue): Queue of activities to process
        store (ActivityStore): Storage for activities
        namespace (str): Namespace for activities
    """

    def __init__(self, store=None, namespace=None) -> None:
        """
        Initialize a new ActivityBus instance.

        Args:
            store (ActivityStore, optional): Custom ActivityStore instance
            namespace (str, optional): Namespace for activities
        """
        self.queue = asyncio.Queue()

        # Use provided store or create default
        if store is not None:
            self.store = store
        elif ActivityStore is not None:
            self.store = ActivityStore()
        else:
            raise ActivityBusError(
                "ActivityStore is required but not provided and couldn't be imported. "
                "Make sure activity-store is installed: https://github.com/DeadWisdom/activity-store"
            )

        self.namespace = namespace

    async def submit(self, activity):
        """
        Validate, store, and enqueue an activity for processing.

        Args:
            activity (dict): The activity to submit

        Returns:
            dict: The processed activity with any additions

        Raises:
            InvalidActivityError: If the activity is invalid
            ActivityIdError: If the activity ID is invalid or can't be generated
        """
        # Validate required fields
        if not isinstance(activity, dict):
            raise InvalidActivityError("Activity must be a dictionary")

        if "actor" not in activity:
            raise InvalidActivityError("Activity must contain 'actor' field")

        if "type" not in activity:
            raise InvalidActivityError("Activity must contain 'type' field")

        # Make a copy to avoid modifying the input
        activity = activity.copy()

        # Set ID if missing
        if "id" not in activity:
            if not self.namespace:
                raise ActivityIdError("Cannot generate ID without namespace")

            actor_id = activity["actor"]
            if isinstance(actor_id, dict) and "id" in actor_id:
                actor_id = actor_id["id"]

            chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
            nano_id = nanoid_generate(chars, 12)
            activity["id"] = f"{self.namespace}/users/{actor_id}/outbox/{nano_id}"

        # Validate ID scope
        actor_id = activity["actor"]
        if isinstance(actor_id, dict) and "id" in actor_id:
            actor_id = actor_id["id"]

        activity_id = activity["id"]
        if not activity_id.startswith(f"{self.namespace}/users/{actor_id}/"):
            raise ActivityIdError(f"Activity ID must be scoped under actor's URI: {activity_id}")

        # Set timestamp if missing
        if "published" not in activity:
            activity["published"] = datetime.now(UTC).isoformat()

        # Initialize result field if not present
        if "result" not in activity:
            activity["result"] = []

        # Store activity
        await self.store.store(activity)

        # Enqueue activity
        await self.queue.put(activity)

        return activity

    async def get_queue_length(self):
        """
        Get the current length of the activity queue.

        Returns:
            int: Number of activities in the queue
        """
        return self.queue.qsize()

    async def process_next(self, no_wait=False):
        """
        Process the next activity from the queue.

        Args:
            no_wait (bool): If True, returns None immediately if queue is empty
                           instead of waiting for an item

        Returns:
            dict: The processed activity, or None if queue is empty
        """
        if no_wait and self.queue.empty():
            return None

        try:
            activity = await self.queue.get()
            return await self.process(activity)
        except asyncio.QueueEmpty:
            return None

    async def process(self, activity):
        """
        Process an activity using matching rules and effects.

        Args:
            activity (dict): The activity to process

        Returns:
            dict: The processed activity with results
        """
        # Ensure activity is dereferenced
        activity = await self.store.dereference(activity)

        # Make a copy to avoid modifying the input directly
        activity = activity.copy()

        # Initialize result field if not present
        if "result" not in activity:
            activity["result"] = []

        try:
            # Load rules from store
            rules = await self.store.query({"type": "Rule"}, collection="/sys/rules")

            # Match rules
            matched_rules = []
            for rule in rules:
                try:
                    match_result = await self.store.frame(activity, rule["match"], require_match=True)

                    if match_result:
                        matched_rules.append(rule)
                except Exception:
                    # Skip rules that failed to match
                    continue

            # Sort matched rules by priority
            matched_rules.sort(key=lambda r: r.get("priority", 100))

            # Execute effects from matched rules
            for rule in matched_rules:
                for effect_id in rule["effect"]:
                    effect_data = registry.get(effect_id)

                    if not effect_data:
                        activity["result"].append(
                            {
                                "type": "Error",
                                "content": f"Effect not found: {effect_id}",
                                "context": activity["id"],
                            }
                        )
                        continue

                    effect_func = effect_data["function"]

                    try:
                        if inspect.iscoroutinefunction(effect_func):
                            effect_result = await effect_func(activity)
                        else:
                            effect_result = effect_func(activity)

                        # If effect returns a result, append it
                        if effect_result:
                            if isinstance(effect_result, list):
                                activity["result"].extend(effect_result)
                            else:
                                activity["result"].append(effect_result)

                    except Exception as e:
                        error_info = {
                            "type": "Error",
                            "content": traceback.format_exc(),
                            "error": str(e),
                            "effect": effect_id,
                            "context": activity["id"],
                        }
                        activity["result"].append(error_info)

            # Check for new activities in the result
            for item in activity["result"]:
                if isinstance(item, dict) and "type" in item and "id" not in item:
                    # This looks like a new activity, submit it
                    if "context" not in item:
                        item["context"] = activity["id"]

                    if "actor" not in item and "actor" in activity:
                        item["actor"] = activity["actor"]

                    try:
                        await self.submit(item)
                    except Exception as e:
                        error_info = {
                            "type": "Error",
                            "content": f"Failed to submit new activity: {e!s}",
                            "context": activity["id"],
                        }
                        activity["result"].append(error_info)

            # Store updated activity
            await self.store.store(activity)

            return activity

        except Exception as e:
            # Handle any unhandled exceptions
            error_info = {
                "type": "Error",
                "content": traceback.format_exc(),
                "error": str(e),
                "context": activity["id"],
            }

            # Add error to results
            if "result" not in activity:
                activity["result"] = []
            activity["result"].append(error_info)

            # Convert to tombstone
            tombstone = await self.store.convert_to_tombstone(activity)

            # Store tombstone
            await self.store.store(tombstone)

            return tombstone

    async def load_rules(self, *folders):
        """
        Load rules from YAML files in the specified folders.

        Args:
            *folders (str): Paths to folders containing rule YAML files

        Returns:
            list: List of stored rule dictionaries
        """
        rules = await load_rules(*folders)

        # Store rules in ActivityStore
        for rule in rules:
            await self.store.store(rule, collection="/sys/rules")

        return rules

    async def load_effects(self, *modules):
        """
        Import modules to load their effects.

        Args:
            *modules (str): Module names to import

        Returns:
            list: List of registered effects
        """
        effects = await load_effects(*modules)

        # Store effects in ActivityStore
        for effect in effects:
            await self.store.store(effect, collection="/sys/effects")

        return effects
