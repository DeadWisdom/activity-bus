# ABOUTME: Provides a central registry for effects used by the ActivityBus
# ABOUTME: Allows for dynamic registration and retrieval of effects

class Registry:
    """A central registry for storing effect functions and their metadata."""
    
    def __init__(self):
        self.effects = {}
    
    def register(self, effect_id, func, priority=100, **metadata):
        """
        Register an effect function with its metadata.
        
        Args:
            effect_id (str): Unique identifier for the effect
            func (callable): The effect function
            priority (int): Execution priority (lower numbers execute first)
            **metadata: Additional metadata for the effect
        """
        self.effects[effect_id] = {
            "id": effect_id,
            "function": func,
            "priority": priority,
            **metadata,
            "type": "Effect"
        }
        return self.effects[effect_id]
    
    def get(self, effect_id):
        """
        Get an effect by its ID.
        
        Args:
            effect_id (str): The effect ID to retrieve
            
        Returns:
            dict: The effect entry, or None if not found
        """
        return self.effects.get(effect_id)
    
    def list_effects(self):
        """
        List all registered effects.
        
        Returns:
            list: List of effect entries (without the function references)
        """
        return [
            {k: v for k, v in effect.items() if k != "function"}
            for effect in self.effects.values()
        ]


# Global registry instance
registry = Registry()