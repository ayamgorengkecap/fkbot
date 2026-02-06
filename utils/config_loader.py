"""Config loader and validator"""
import json
import os

def load_config(config_path):
    """Load and validate config file"""
    if not os.path.exists(config_path):
        return None
    
    try:
        with open(config_path) as f:
            return json.load(f)
    except json.JSONDecodeError:
        return None

def save_config(config_path, config):
    """Save config to file"""
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

def validate_account_config(config):
    """Validate account config structure"""
    errors = []
    
    if not config.get('credentials'):
        errors.append("Missing credentials")
    
    if not config.get('proxy'):
        errors.append("Missing proxy")
    
    return len(errors) == 0, errors
