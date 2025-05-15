import pytest
import tempfile
import os
from pathlib import Path

from activity_bus.rules import validate_rule, load_rules
from activity_bus.errors import RuleLoadError


def test_validate_rule():
    """Test validating a rule with correct structure."""
    valid_rule = {
        "id": "test.rule",
        "match": {"type": "Test"},
        "effect": ["test.effect"]
    }
    
    # Should not raise an exception
    validated = validate_rule(valid_rule)
    assert validated["priority"] == 100  # Default priority
    assert validated["type"] == "Rule"   # Default type
    
    # Test with single effect string
    single_effect_rule = {
        "id": "test.rule",
        "match": {"type": "Test"},
        "effect": "test.effect"
    }
    validated = validate_rule(single_effect_rule)
    assert validated["effect"] == ["test.effect"]  # Converted to list
    
    # Test with custom priority and type
    custom_rule = {
        "id": "test.rule",
        "match": {"type": "Test"},
        "effect": ["test.effect"],
        "priority": 50,
        "type": "CustomRule"
    }
    validated = validate_rule(custom_rule)
    assert validated["priority"] == 50
    assert validated["type"] == "CustomRule"


def test_validate_rule_invalid():
    """Test validating invalid rules."""
    # Missing required fields
    missing_id = {"match": {"type": "Test"}, "effect": ["test.effect"]}
    with pytest.raises(RuleLoadError):
        validate_rule(missing_id)
    
    missing_match = {"id": "test.rule", "effect": ["test.effect"]}
    with pytest.raises(RuleLoadError):
        validate_rule(missing_match)
    
    missing_effect = {"id": "test.rule", "match": {"type": "Test"}}
    with pytest.raises(RuleLoadError):
        validate_rule(missing_effect)
    
    # Invalid types
    invalid_match = {"id": "test.rule", "match": "not_a_dict", "effect": ["test.effect"]}
    with pytest.raises(RuleLoadError):
        validate_rule(invalid_match)
    
    invalid_effect = {"id": "test.rule", "match": {"type": "Test"}, "effect": 123}
    with pytest.raises(RuleLoadError):
        validate_rule(invalid_effect)
    
    # Not a dictionary
    with pytest.raises(RuleLoadError):
        validate_rule("not_a_dict")


@pytest.mark.asyncio
async def test_load_rules():
    """Test loading rules from YAML files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a valid rule file
        valid_rule_yaml = """
id: test.rule1
match:
  type: Test1
effect:
  - test.effect1
"""
        valid_rule_path = Path(temp_dir) / "valid_rule.yaml"
        with open(valid_rule_path, "w") as f:
            f.write(valid_rule_yaml)
        
        # Create a file with multiple rules
        multiple_rules_yaml = """
- id: test.rule2
  match:
    type: Test2
  effect:
    - test.effect2
  
- id: test.rule3
  match:
    type: Test3
  effect:
    - test.effect3
  priority: 50
"""
        multiple_rules_path = Path(temp_dir) / "multiple_rules.yaml"
        with open(multiple_rules_path, "w") as f:
            f.write(multiple_rules_yaml)
        
        # Create an invalid rule file
        invalid_rule_yaml = """
id: test.invalid
match: not_a_dict
effect:
  - test.effect
"""
        invalid_rule_path = Path(temp_dir) / "invalid_rule.yaml"
        with open(invalid_rule_path, "w") as f:
            f.write(invalid_rule_yaml)
        
        # Create a subfolder with a rule
        subfolder = Path(temp_dir) / "subfolder"
        os.makedirs(subfolder)
        subfolder_rule_yaml = """
id: test.subfolder_rule
match:
  type: SubfolderTest
effect:
  - test.subfolder_effect
"""
        subfolder_rule_path = subfolder / "subfolder_rule.yaml"
        with open(subfolder_rule_path, "w") as f:
            f.write(subfolder_rule_yaml)
        
        # Test loading valid rules
        rules = await load_rules(temp_dir)
        assert len(rules) == 4  # 1 + 2 + 1 from subfolder
        
        # Verify loaded rules
        rule_ids = [rule["id"] for rule in rules]
        assert "test.rule1" in rule_ids
        assert "test.rule2" in rule_ids
        assert "test.rule3" in rule_ids
        assert "test.subfolder_rule" in rule_ids
        
        # Find rule3 and check its priority
        rule3 = next(rule for rule in rules if rule["id"] == "test.rule3")
        assert rule3["priority"] == 50
        
        # Test loading non-existent folder
        with pytest.raises(RuleLoadError):
            await load_rules("/nonexistent/folder")