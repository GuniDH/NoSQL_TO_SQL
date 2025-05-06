"""
Utility functions for the JSON to CSV converter.
"""
import json
import os
import functools
import inspect
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Union, Callable, TypeVar

def secure_paths(func):
    """
    Smart decorator that checks all parameters that look like file paths.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get function signature
        sig = inspect.signature(func)
        
        # Bind arguments to parameter names
        bound_args = sig.bind(*args, **kwargs)
        
        # Safe directories
        safe_dirs = [
            os.path.abspath(os.getcwd()),  
            os.path.abspath(tempfile.gettempdir())
        ]
        
        # Check each parameter
        for param_name, value in bound_args.arguments.items():
            # Only check parameters with 'path' in the name and that are strings
            if 'path' in param_name.lower() and isinstance(value, str):
                abs_path = os.path.abspath(value)
                
                # Check if path is in a safe directory
                if not any(abs_path == safe_dir or abs_path.startswith(safe_dir + os.sep) 
                          for safe_dir in safe_dirs):
                    raise ValueError(f"Security error: Path '{value}' points outside allowed directories")
        
        # Call the original function
        return func(*args, **kwargs)
    return wrapper


def detect_json_structure(json_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze the structure of JSON data to detect schemas, types, and nested elements.
    
    Args:
        json_data: List of JSON objects
        
    Returns:
        Dictionary with structure information
    """
    schema = {}
    
    # Function to recursively analyze structure
    def analyze_value(value, current_schema=None):
        if current_schema is None:
            current_schema = {}
            
        if isinstance(value, dict):
            for k, v in value.items():
                if k not in current_schema:
                    current_schema[k] = {"type": set(), "nested": None}
                
                # Add type
                current_schema[k]["type"].add(type(v).__name__)
                
                # Recursive analysis for nested structures
                if isinstance(v, (dict, list)):
                    if current_schema[k]["nested"] is None:
                        if isinstance(v, dict):
                            current_schema[k]["nested"] = {}
                        else:
                            current_schema[k]["nested"] = {"array_items": {}}
                    
                    if isinstance(v, dict):
                        analyze_value(v, current_schema[k]["nested"])
                    elif isinstance(v, list) and v and isinstance(v[0], dict):
                        analyze_value(v[0], current_schema[k]["nested"]["array_items"])
        
        return current_schema
    
    # Analyze each item in the JSON data
    for item in json_data:
        schema = analyze_value(item, schema)
    
    # Convert type sets to lists for JSON serialization
    def convert_types(node):
        if isinstance(node, dict):
            for k, v in list(node.items()):
                if k == "type" and isinstance(v, set):
                    node[k] = sorted(list(v))
                elif isinstance(v, dict):
                    convert_types(v)
    
    convert_types(schema)
    return schema


@secure_paths
def validate_json_path(file_path: str) -> bool:
    """
    Validate if the file exists and contains valid JSON.
    
    Args:
        file_path: Path to the JSON file (relative or absolute)
        
    Returns:
        True if valid, False otherwise
    """
    # Path is already checked for security by the decorator
    if not os.path.exists(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            json.load(file)
        return True
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False


def get_output_path(input_path: str, mode: str = "flattened") -> str:
    """
    Generate an output path based on the input path.
    
    Args:
        input_path: Path to the input JSON file
        mode: Conversion mode
        
    Returns:
        Suggested output path (preserving relative/absolute format)
    """
    # Extract base name and directory while preserving path format
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    directory = os.path.dirname(input_path)
    
    # Create output path with same format (relative/absolute) as input
    if mode == "flattened":
        return os.path.join(directory, f"{base_name}.csv")
    else:
        return os.path.join(directory, f"{base_name}_csvs")