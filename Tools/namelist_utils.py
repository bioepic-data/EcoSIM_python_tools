import re
import os
import yaml
from typing import Dict, Optional

def update_namelist(namelist_path: str, updates: Dict[str, str]) -> None:
    """
    Update a Fortran namelist file with new values for specific keys.

    Args:
        namelist_path: Path to the .namelist file.
        updates: Dictionary of key:value pairs to update.
    """
    if not os.path.exists(namelist_path):
        print(f"Namelist file not found: {namelist_path}")
        return

    with open(namelist_path, 'r') as f:
        content = f.read()

    for key, value in updates.items():
        # Regex to find key = 'value' or key = value
        # Handles optional spaces and different quote types
        pattern = rf"({key}\s*=\s*['\"]?)([^'\"\s,/\n]+)(['\"]?)"
        replacement = rf"\1{value}\3"
        content = re.sub(pattern, replacement, content)

    with open(namelist_path, 'w') as f:
        f.write(content)

def record_forcing_yaml(yaml_path: str, data: Dict[str, str]) -> None:
    """
    Record forcing file paths in a YAML file.
    """
    os.makedirs(os.path.dirname(yaml_path), exist_ok=True)
    with open(yaml_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)
