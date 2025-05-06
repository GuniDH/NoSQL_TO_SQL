"""
Pytest configuration for json2csv tests.
"""
import json
import os
import tempfile

import pytest


@pytest.fixture(scope="session")
def sample_complex_json():
    """
    Create a more complex JSON structure for testing.
    This sample includes more nested objects, arrays, and mixed data types.
    """
    return [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30,
            "address": {
                "street": "123 Main St",
                "city": "Boston",
                "state": "MA",
                "zip": "02118"
            },
            "preferences": {
                "newsletter": True,
                "notifications": {
                    "email": True,
                    "sms": False
                }
            },
            "hobbies": ["reading", "swimming", "coding"],
            "orders": [
                {"id": 101, "total": 50.00, "date": "2024-01-15"},
                {"id": 102, "total": 75.50, "date": "2024-02-01"}
            ]
        },
        {
            "id": 2,
            "name": "Jane Smith",
            "email": "jane@example.com",
            "age": 25,
            "address": {
                "street": "456 Oak Ave",
                "city": "New York",
                "state": "NY",
                "zip": None
            },
            "preferences": {
                "newsletter": False,
                "notifications": {
                    "email": False,
                    "sms": True
                }
            },
            "hobbies": ["painting"],
            "orders": []
        },
        {
            "id": 3,
            "name": "Bob Johnson",
            "email": "bob@example.com",
            "age": 45,
            "preferences": {
                "newsletter": True
            },
            "hobbies": [],
            "orders": [
                {"id": 103, "total": 25.00, "date": "2024-01-20"}
            ]
        }
    ]


@pytest.fixture(scope="session")
def complex_json_file(sample_complex_json):
    """Create a temporary file with complex JSON data."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as temp:
        json.dump(sample_complex_json, temp)
        temp_path = temp.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)