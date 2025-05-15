# Example script demonstrating usage of ActivityBus with sample activities
# Shows how to submit and process activities with rules and effects

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path to import activity_bus
sys.path.insert(0, str(Path(__file__).parent.parent))

from activity_bus import ActivityBus

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("activity_bus_example")


async def main() -> None:
    # Initialize the ActivityBus
    bus = ActivityBus(namespace="https://example.com")

    # Load example effects and rules
    logger.info("Loading effects and rules...")
    await bus.load_effects("examples.effects")
    await bus.load_rules(str(Path(__file__).parent / "rules"))

    # Create sample activities
    activities = [
        # Create a Note
        {
            "type": "Create",
            "actor": "user1",
            "object": {"type": "Note", "content": "Hello, ActivityBus! #testing #activitystreams"},
        },
        # A standalone Note
        {"type": "Note", "actor": "user2", "content": "This is a direct Note activity with #hashtags"},
        # Follow another user
        {"type": "Follow", "actor": "user1", "object": "user3"},
    ]

    # Submit all activities
    logger.info("Submitting activities...")
    for activity in activities:
        logger.info(f"Submitting {activity['type']} activity")
        await bus.submit(activity)

    # Process all activities
    logger.info("Processing activities...")
    while not bus.queue.empty():
        processed = await bus.process_next()

        if processed:
            activity_id = processed.get("id", "unknown")
            activity_type = processed.get("type", "unknown")
            logger.info(f"Processed {activity_type} (ID: {activity_id})")

            # Show results
            if "result" in processed:
                logger.info(f"Results: {processed['result']}")

    logger.info("All activities processed!")


if __name__ == "__main__":
    asyncio.run(main())
