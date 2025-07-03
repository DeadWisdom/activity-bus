"""
This module contains the core ActivityBus class for processing Activity Streams 2.0 activities.
"""

import asyncio
import datetime
import traceback
import uuid
from typing import Any

try:
    from activity_store import ActivityStore
    from activity_store.ld import frame
except ImportError as err:
    raise ImportError("ActivityStore is required for ActivityBus. Install it via: pip install activity-store") from err

from .behaviors import get_all_behaviors
from .errors import (
    ActivityIdError,
    BehaviorExecutionError,
    InvalidActivityError,
)


class ActivityBus:
    """
    Main class for processing Activity Streams 2.0 activities via a rule-based engine.
    """

    def __init__(self, store: ActivityStore | None = None, namespace: str = "activity_bus"):
        """
        Initialize a new ActivityBus instance.

        Args:
            store: Optional ActivityStore instance, if not provided a new one will be created
            namespace: Optional namespace for the bus, used in generated IDs
        """
        # Initialize queue for async processing
        self.queue = asyncio.Queue()

        # Initialize store
        self.store = store or ActivityStore()

        # Set namespace
        self.namespace = namespace

    async def submit(self, activity: dict[str, Any]) -> dict[str, Any]:
        """
        Submit an activity for processing.

        Args:
            activity: The activity to submit, must contain at minimum an 'actor' and 'type'

        Returns:
            The validated and possibly modified activity with guaranteed ID and timestamp

        Raises:
            InvalidActivityError: If the activity is missing required fields
            ActivityIdError: If the activity ID is invalid or not properly scoped
        """
        # Make a copy of the activity to avoid modifying the original
        activity = activity.copy()

        # Validate required fields
        if "actor" not in activity:
            raise InvalidActivityError("Activity must contain an 'actor' field")

        if "type" not in activity:
            raise InvalidActivityError("Activity must contain a 'type' field")

        # Set ID if missing
        if "id" not in activity:
            raise InvalidActivityError("Activity must have an 'id'")

        # Set timestamp if missing
        if "published" not in activity:
            activity["published"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Initialize result field if not present
        if "result" not in activity:
            activity["result"] = []

        # Store the activity
        await self.store.store(activity)

        # Enqueue for processing
        self.queue.put_nowait(activity)

        return activity

    async def process_next(self) -> dict[str, Any] | None:
        """
        Process the next activity in the queue.

        Returns:
            The processed activity or None if the queue is empty

        Raises:
            BehaviorExecutionError: If there's an error executing a behavior (wrapped in the activity result)
        """
        # Get the next activity from the queue
        try:
            activity = self.queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

        # Process the activity
        processed_activity = await self.process(activity)

        # Mark the task as done
        self.queue.task_done()

        return processed_activity

    async def process(self, activity: dict[str, Any]) -> dict[str, Any]:
        """
        Process an activity by matching and executing behaviors.

        Args:
            activity: The activity to process

        Returns:
            The processed activity with updated result field

        Raises:
            BehaviorExecutionError: If there's an error executing a behavior (wrapped in the activity result)
        """
        try:
            # Ensure activity has a result field
            if "result" not in activity:
                activity["result"] = []

            # Get all behaviors
            behaviors = get_all_behaviors()

            # Match behaviors and execute
            for behavior_id, behavior_data in behaviors.items():
                # Try to match the activity with the behavior's pattern
                if frame(activity, behavior_data["when"], require_match=True):
                    try:
                        # Execute the behavior
                        function = behavior_data["_function"]
                        result = function(activity)

                        # Handle potential new activities to submit
                        if isinstance(result, list):
                            for new_activity in result:
                                if isinstance(new_activity, dict) and "type" in new_activity:
                                    # Set context to current activity ID
                                    if "context" not in new_activity:
                                        new_activity["context"] = activity["id"]

                                    # Submit the new activity
                                    await self.submit(new_activity)

                    except Exception as e:
                        # Add the error to the result
                        error = {
                            "type": "Error",
                            "content": traceback.format_exc(),
                            "context": activity["id"],
                            "error_type": type(e).__name__,
                        }
                        activity["result"].append(error)

                        # Raise a BehaviorExecutionError, but we'll catch it below
                        raise BehaviorExecutionError(f"Error executing behavior {behavior_id}") from e

            # Store the processed activity
            await self.store.store(activity)

            return activity

        except Exception as e:
            # Add the error to the result if not already added
            error_added = False
            for res in activity.get("result", []):
                if isinstance(res, dict) and res.get("type") == "Error" and res.get("context") == activity.get("id"):
                    error_added = True
                    break

            if not error_added:
                error = {
                    "type": "Error",
                    "content": traceback.format_exc(),
                    "context": activity.get("id", "unknown"),
                    "error_type": type(e).__name__,
                }
                if "result" not in activity:
                    activity["result"] = []
                activity["result"].append(error)

            # Convert activity to tombstone
            tombstone = await self.store.convert_to_tombstone(activity)

            # Store the tombstone
            await self.store.store(tombstone)

            return tombstone
