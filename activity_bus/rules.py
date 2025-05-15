# ABOUTME: Handles loading and validation of rules from YAML files
# ABOUTME: Provides utilities for rule management within the ActivityBus

import os
import yaml
from pathlib import Path

from .errors import RuleLoadError


def validate_rule(rule):
    """
    Validate that a rule has the required structure.
    
    Args:
        rule (dict): The rule to validate
        
    Raises:
        RuleLoadError: If the rule is invalid
    """
    if not isinstance(rule, dict):
        raise RuleLoadError("Rule must be a dictionary")
    
    required_fields = ["id", "match", "effect"]
    for field in required_fields:
        if field not in rule:
            raise RuleLoadError(f"Rule is missing required field: {field}")
    
    if not isinstance(rule["match"], dict):
        raise RuleLoadError("Rule 'match' field must be a dictionary")
    
    if not isinstance(rule["effect"], list):
        if isinstance(rule["effect"], str):
            # Convert single effect to list
            rule["effect"] = [rule["effect"]]
        else:
            raise RuleLoadError("Rule 'effect' field must be a list or string")
    
    # Set defaults
    if "priority" not in rule:
        rule["priority"] = 100
    
    if "type" not in rule:
        rule["type"] = "Rule"
    
    return rule


async def load_rules(*folders):
    """
    Load rules from YAML files in the specified folders.
    
    Args:
        *folders (str): Paths to folders containing rule YAML files
        
    Returns:
        list: List of validated rule dictionaries
        
    Raises:
        RuleLoadError: If a rule couldn't be loaded or is invalid
    """
    rules = []
    
    for folder in folders:
        folder_path = Path(folder)
        
        if not folder_path.exists() or not folder_path.is_dir():
            raise RuleLoadError(f"Rule folder does not exist: {folder}")
        
        for file_path in folder_path.glob("**/*.yaml"):
            try:
                with open(file_path, "r") as f:
                    rule_data = yaml.safe_load(f)
                    
                if isinstance(rule_data, list):
                    # Multiple rules in one file
                    for rule in rule_data:
                        rules.append(validate_rule(rule))
                else:
                    # Single rule
                    rules.append(validate_rule(rule_data))
                    
            except yaml.YAMLError as e:
                raise RuleLoadError(f"Failed to parse YAML file {file_path}: {str(e)}")
            except Exception as e:
                raise RuleLoadError(f"Error loading rule file {file_path}: {str(e)}")
    
    return rules