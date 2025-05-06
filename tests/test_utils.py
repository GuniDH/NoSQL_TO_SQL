"""
Tests for the utils module.
"""
import json
import os
import tempfile

import pytest

from json2csv.utils import (
    detect_json_structure,
    validate_json_path,
    get_output_path,
)


# Sample test data
SAMPLE_JSON_DATA = [
    {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "address": {
            "street": "123 Main St",
            "city": "Boston"
        },
        "tags": ["customer", "premium"]
    },
    {
        "id": 2,
        "name": "Jane Smith",
        "email": "jane@example.com",
        "address": {
            "street": "456 Oak Ave",
            "city": "New York"
        },
        "tags": ["customer"]
    }
]

@pytest.fixture
def sample_json_file():
    """Create a temporary JSON file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as temp:
        json.dump(SAMPLE_JSON_DATA, temp)
        temp_path = temp.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


def test_detect_json_structure():
    """Test detecting the structure of JSON data."""
    structure = detect_json_structure(SAMPLE_JSON_DATA)
    
    # Check that top-level fields are detected
    assert "id" in structure
    assert "name" in structure
    assert "email" in structure
    assert "address" in structure
    assert "tags" in structure
    
    # Check that nested fields are detected
    assert structure["address"]["nested"] is not None
    assert "city" in structure["address"]["nested"]
    assert "street" in structure["address"]["nested"]
    
    # Check that types are detected correctly
    assert "int" in structure["id"]["type"]
    assert "str" in structure["name"]["type"]
    assert "list" in structure["tags"]["type"]
    assert "dict" in structure["address"]["type"]


def test_validate_json_path(sample_json_file):
    """Test validating a JSON file path."""
    # Valid path
    assert validate_json_path(sample_json_file) is True
    
    # Invalid path
    assert validate_json_path("nonexistent.json") is False
    
    # Invalid JSON content
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp:
        temp.write(b"This is not valid JSON")
        invalid_path = temp.name
    
    try:
        assert validate_json_path(invalid_path) is False
    finally:
        if os.path.exists(invalid_path):
            os.remove(invalid_path)


def test_get_output_path():
    """Test generating output paths."""
    # Use os.path.join to create platform-specific paths
    input_path = os.path.join("/path", "to", "data.json")
    
    # Test flattened mode
    flattened_path = get_output_path(input_path, "flattened")
    expected_flattened = os.path.join("/path", "to", "data.csv")
    assert flattened_path == expected_flattened
    
    # Test normalized mode
    normalized_path = get_output_path(input_path, "normalized")
    expected_normalized = os.path.join("/path", "to", "data_csvs")
    assert normalized_path == expected_normalized