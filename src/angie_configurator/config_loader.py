import os
import yaml
from typing import List, Dict, Tuple
from pydantic import ValidationError
from .schema import DomainConfig

def find_yaml_files(directory: str) -> List[str]:
    """Find all .yaml and .yml files in the given directory."""
    yaml_files = []
    if not os.path.exists(directory):
        return yaml_files
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(('.yaml', '.yml')):
                yaml_files.append(os.path.join(root, file))
    return yaml_files

def load_and_validate_yaml(filepath: str) -> Tuple[DomainConfig, str]:
    """Load and validate a single YAML file."""
    with open(filepath, 'r') as f:
        try:
            data = yaml.safe_load(f)
            if not isinstance(data, dict):
                return None, f"Invalid YAML format in {filepath}: expected a dictionary."
            config = DomainConfig(**data)
            return config, None
        except yaml.YAMLError as e:
            return None, f"YAML parsing error in {filepath}: {e}"
        except ValidationError as e:
            return None, f"Validation error in {filepath}:\n{e}"
        except Exception as e:
            return None, f"Unexpected error loading {filepath}: {e}"

def load_all_configs(directory: str) -> Tuple[List[DomainConfig], List[str]]:
    """Load all valid configs from a directory, returning configs and errors."""
    configs = []
    errors = []
    for filepath in find_yaml_files(directory):
        config, error = load_and_validate_yaml(filepath)
        if config:
            configs.append(config)
        if error:
            errors.append(error)
    return configs, errors
