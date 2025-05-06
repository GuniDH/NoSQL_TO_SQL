"""
Tests for the converter module.
"""
import json
import os
import tempfile
import csv
from pathlib import Path

import pytest

from json2csv.converter import (
    read_json,
    flatten_json,
    convert_to_flattened_csv,
    convert_to_normalized_csvs,
    convert_json_to_csv,
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


def test_read_json(sample_json_file):
    """Test reading JSON from a file."""
    data = read_json(sample_json_file)
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["name"] == "John Doe"
    assert data[1]["name"] == "Jane Smith"


def test_flatten_json():
    """Test flattening a nested JSON object."""
    sample = {
        "id": 1,
        "name": "John",
        "address": {
            "city": "Boston",
            "zip": "02118"
        },
        "tags": ["a", "b"]
    }
    
    flattened = flatten_json(sample, "/")
    
    assert flattened["id"] == 1
    assert flattened["name"] == "John"
    assert flattened["address/city"] == "Boston"
    assert flattened["address/zip"] == "02118"
    assert flattened["tags/0"] == "a"
    assert flattened["tags/1"] == "b"


def test_convert_to_flattened_csv():
    """Test conversion to a flattened CSV."""
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp:
        output_path = temp.name
    
    try:
        convert_to_flattened_csv(SAMPLE_JSON_DATA, output_path)
        
        # Verify the CSV file was created
        assert os.path.exists(output_path)
        
        # Read back the CSV and verify contents
        rows = []
        with open(output_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                rows.append(row)
        
        assert len(rows) == 2
        assert rows[0]["name"] == "John Doe"
        assert rows[0]["address/city"] == "Boston"
        assert rows[1]["name"] == "Jane Smith"
        assert rows[1]["address/city"] == "New York"
        
    finally:
        # Cleanup
        if os.path.exists(output_path):
            os.remove(output_path)


def test_convert_to_normalized_csvs():
    """Test conversion to normalized CSVs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        convert_to_normalized_csvs(SAMPLE_JSON_DATA, temp_dir)
        
        # Verify root.csv exists and has correct content
        root_path = os.path.join(temp_dir, "root.csv")
        assert os.path.exists(root_path)
        
        # Read back the CSV and verify contents
        with open(root_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]["name"] == "John Doe"
        assert rows[0]["email"] == "john@example.com"
        
        # Verify address.csv exists and has correct content
        address_path = os.path.join(temp_dir, "address.csv")
        assert os.path.exists(address_path)
        
        with open(address_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]["city"] == "Boston"
        assert rows[1]["city"] == "New York"


def test_convert_json_to_csv_flattened(sample_json_file):
    """Test the main conversion function in flattened mode."""
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp:
        output_path = temp.name
    
    try:
        convert_json_to_csv(sample_json_file, output_path, "flattened")
        
        # Verify the CSV file was created
        assert os.path.exists(output_path)
        
        # Read back the CSV and verify contents
        with open(output_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]["name"] == "John Doe"
        
    finally:
        # Cleanup
        if os.path.exists(output_path):
            os.remove(output_path)


def test_convert_json_to_csv_normalized(sample_json_file):
    """Test the main conversion function in normalized mode."""
    with tempfile.TemporaryDirectory() as temp_dir:
        convert_json_to_csv(sample_json_file, temp_dir, "normalized")
        
        # Verify root.csv exists
        root_path = os.path.join(temp_dir, "root.csv")
        assert os.path.exists(root_path)
        
        # Verify address.csv exists
        address_path = os.path.join(temp_dir, "address.csv")
        assert os.path.exists(address_path)


def test_invalid_mode(sample_json_file):
    """Test that an invalid mode raises a ValueError."""
    with pytest.raises(ValueError):
        convert_json_to_csv(sample_json_file, "output.csv", "invalid_mode")