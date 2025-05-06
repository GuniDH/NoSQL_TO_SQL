"""
Core module for converting JSON data to CSV format.
Supports both flattened (single CSV) and normalized (multiple CSV) approaches.
"""
import csv
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Union

from json2csv.utils import secure_paths


@secure_paths
def read_json(file_path: str) -> List[Dict[str, Any]]:
    """
    Read JSON data from file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        List of dictionaries representing the JSON data
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Ensure data is a list of dictionaries
    if isinstance(data, dict):
        data = [data]
    elif not isinstance(data, list):
        raise ValueError("JSON data must be either a dictionary or a list of dictionaries")
    
    return data


def flatten_json(obj: Dict[str, Any], separator: str = "/") -> Dict[str, Any]:
    """
    Flatten a nested JSON object into a single-level dictionary.
    
    Args:
        obj: The nested JSON object
        separator: Separator for nested keys
        
    Returns:
        A flattened dictionary with compound keys
    """
    result = {}
    
    def _flatten(item, prefix=''):
        if isinstance(item, dict):
            for key, value in item.items():
                _flatten(value, f"{prefix}{key}{separator}" if prefix else f"{key}{separator}")
        elif isinstance(item, list):
            for i, value in enumerate(item):
                if isinstance(value, (dict, list)):
                    _flatten(value, f"{prefix}{i}{separator}")
                else:
                    result[f"{prefix}{i}"] = value
        else:
            # Remove the trailing separator
            if prefix:
                prefix = prefix[:-1]
            result[prefix] = item
    
    _flatten(obj)
    return result


@secure_paths
def convert_to_flattened_csv(json_data: List[Dict[str, Any]], output_path: str, separator: str = "/") -> None:
    """
    Convert JSON data to a single flattened CSV file.
    
    Args:
        json_data: List of JSON objects
        output_path: Path to the output CSV file
        separator: Separator for nested keys
        
    Returns:
        None
    """
    # Flatten each JSON object
    flattened_data = [flatten_json(item, separator) for item in json_data]
    
    # Get all unique keys to create headers
    all_keys = set()
    for item in flattened_data:
        all_keys.update(item.keys())
    
    # Sort keys for consistent output
    headers = sorted(all_keys)
    
    # Ensure the output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Write to CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for item in flattened_data:
            writer.writerow(item)


def extract_entity_structure(
    json_data: List[Dict[str, Any]]
) -> Dict[str, Dict[str, List[str]]]:
    """
    Analyze JSON data to extract the entity structure for normalization.
    
    Args:
        json_data: List of JSON objects
        
    Returns:
        Dictionary of entity definitions with their fields and relationships
    """
    entities = {"root": {"fields": set(), "relations": {}}}
    
    # First pass: identify entities and their fields
    for item in json_data:
        for key, value in item.items():
            if isinstance(value, dict):
                # This is a nested object, create a new entity
                if key not in entities:
                    entities[key] = {"fields": set(), "relations": {}}
                for sub_key, sub_value in value.items():
                    if not isinstance(sub_value, (dict, list)):
                        entities[key]["fields"].add(sub_key)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                # This is a list of objects, create a new entity
                if key not in entities:
                    entities[key] = {"fields": set(), "relations": {}}
                # Add fields from the first item as a sample
                for sub_key, sub_value in value[0].items():
                    if not isinstance(sub_value, (dict, list)):
                        entities[key]["fields"].add(sub_key)
                # Mark this as a one-to-many relationship
                entities["root"]["relations"][key] = "one_to_many"
            else:
                # Simple field
                entities["root"]["fields"].add(key)
    
    # Convert sets to sorted lists for consistent output
    for entity in entities.values():
        entity["fields"] = sorted(entity["fields"])
    
    return entities


@secure_paths
def convert_to_normalized_csvs(json_data: List[Dict[str, Any]], output_dir: str) -> None:
    """
    Convert JSON data to multiple normalized CSV files.
    
    Args:
        json_data: List of JSON objects
        output_dir: Directory for the output CSV files
        
    Returns:
        None
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract entity structure
    entities = extract_entity_structure(json_data)
    
    # Create root table
    root_data = []
    for i, item in enumerate(json_data):
        row = {"id": i + 1}  # Generate a primary key
        for key, value in item.items():
            if not isinstance(value, (dict, list)):
                row[key] = value
        root_data.append(row)
    
    # Write root table
    root_path = os.path.join(output_dir, "root.csv")
    write_csv(root_path, root_data)
    
    # Process nested entities
    for entity_name, entity_def in entities.items():
        if entity_name == "root":
            continue
        
        entity_data = []
        for i, item in enumerate(json_data):
            if entity_name in item:
                value = item[entity_name]
                if isinstance(value, dict):
                    # One-to-one relationship
                    row = {"id": len(entity_data) + 1, "root_id": i + 1}
                    for field in entity_def["fields"]:
                        if field in value:
                            row[field] = value[field]
                    entity_data.append(row)
                elif isinstance(value, list) and value and isinstance(value[0], dict):
                    # One-to-many relationship
                    for j, sub_item in enumerate(value):
                        row = {"id": len(entity_data) + 1, "root_id": i + 1}
                        for field in entity_def["fields"]:
                            if field in sub_item:
                                row[field] = sub_item[field]
                        entity_data.append(row)
        
        # Write entity table
        entity_path = os.path.join(output_dir, f"{entity_name}.csv")
        write_csv(entity_path, entity_data)


@secure_paths
def write_csv(file_path: str, data: List[Dict[str, Any]]) -> None:
    """
    Write data to a CSV file.
    
    Args:
        file_path: Path to the output CSV file
        data: List of dictionaries to write
        
    Returns:
        None
    """
    if not data:
        return
    
    headers = set()
    for item in data:
        headers.update(item.keys())
    
    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=sorted(headers))
        writer.writeheader()
        for item in data:
            writer.writerow(item)


def convert_json_to_csv(
    input_path: str,
    output_path: str,
    mode: str = "flattened",
    separator: str = "/"
) -> None:
    """
    Main function to convert JSON to CSV.
    
    Args:
        input_path: Path to the input JSON file
        output_path: Path to the output CSV file or directory
        mode: Conversion mode ("flattened" or "normalized")
        separator: Separator for nested keys (only used in flattened mode)
        
    Returns:
        None
        
    Raises:
        ValueError: If mode is invalid
    """
    # Read JSON data
    json_data = read_json(input_path)
    
    # Convert based on selected mode
    if mode == "flattened":
        convert_to_flattened_csv(json_data, output_path, separator)
    elif mode == "normalized":
        # For normalized mode, output_path should be a directory
        output_dir = output_path
        if Path(output_dir).suffix:  # If output_path has an extension
            output_dir = str(Path(output_path).parent / Path(output_path).stem)
        convert_to_normalized_csvs(json_data, output_dir)
    else:
        raise ValueError(f"Invalid mode: {mode}. Choose either 'flattened' or 'normalized'")