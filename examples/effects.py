# Example effects module demonstrating different effect functions
# Used by ActivityBus examples to showcase rule-based activity processing

import logging

from activity_bus import effect

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("example_effects")


@effect(priority=10)
def log_activity(activity):
    """Log information about any activity."""
    activity_id = activity.get("id", "unknown")
    activity_type = activity.get("type", "unknown")

    logger.info(f"Processing activity: {activity_type} (ID: {activity_id})")

    return {"type": "Log", "content": f"Activity logged: {activity_type}", "context": activity.get("id")}


@effect(priority=50)
def process_create(activity):
    """Process a Create activity."""
    logger.info(f"Processing Create activity: {activity.get('id')}")

    # Get the created object
    created_object = activity.get("object")
    if not created_object:
        return {"type": "Error", "content": "Create activity missing 'object' field", "context": activity.get("id")}

    # Just log what was created
    object_type = created_object.get("type", "unknown")
    logger.info(f"Created object of type: {object_type}")

    return {"type": "Log", "content": f"Created {object_type} processed", "context": activity.get("id")}


@effect(priority=50)
def process_note(activity):
    """Process a Note activity."""
    logger.info(f"Processing Note activity: {activity.get('id')}")

    # Get the note content
    content = activity.get("content", "")
    if not content:
        return {"type": "Warning", "content": "Note has no content", "context": activity.get("id")}

    # Check for hashtags
    hashtags = [word[1:] for word in content.split() if word.startswith("#")]

    if hashtags:
        logger.info(f"Found hashtags: {hashtags}")
        return {"type": "HashtagResult", "tags": hashtags, "context": activity.get("id")}

    return {"type": "Log", "content": "Note processed", "context": activity.get("id")}


@effect(priority=50)
def process_follow(activity):
    """Process a Follow activity."""
    logger.info(f"Processing Follow activity: {activity.get('id')}")

    # Get the follow target
    follow_target = activity.get("object")
    if not follow_target:
        return {"type": "Error", "content": "Follow activity missing 'object' field", "context": activity.get("id")}

    # In a real implementation, this would update the follower relationship
    target_id = follow_target if isinstance(follow_target, str) else follow_target.get("id")
    follower_id = activity.get("actor")

    if isinstance(follower_id, dict):
        follower_id = follower_id.get("id")

    logger.info(f"User {follower_id} is now following {target_id}")

    return {"type": "FollowResult", "follower": follower_id, "following": target_id, "context": activity.get("id")}


@effect(priority=60)
async def notify_follow_target(activity):
    """Notify a user that they have a new follower."""
    # Get the follow target
    follow_target = activity.get("object")
    if not follow_target:
        return None

    target_id = follow_target if isinstance(follow_target, str) else follow_target.get("id")
    follower_id = activity.get("actor")

    if isinstance(follower_id, dict):
        follower_id = follower_id.get("id")

    # In a real implementation, this would send a notification
    logger.info(f"Notifying {target_id} about new follower {follower_id}")

    # Create a notification activity to be processed
    return {
        "type": "Notification",
        "actor": "system",
        "to": [target_id],
        "object": {"type": "Follow", "actor": follower_id, "object": target_id},
        "summary": f"New follower: {follower_id}",
    }
