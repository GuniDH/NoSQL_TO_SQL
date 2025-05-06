# JSON to CSV Converter - Guni Deyo Haness

A Python CLI application that converts JSON data files (mimicking MongoDB collections) to CSV format (SQL-like tabular data).

## Overview

This tool addresses the challenge of converting hierarchical NoSQL data structures to flat SQL-like tables. It offers two conversion approaches:

1. **Flattened Mode** (default): Converts the JSON to a single CSV file with nested structures flattened using a separator.
2. **Normalized Mode**: Converts the JSON to multiple CSV files representing a normalized relational database schema with proper relationships.

## Features

- **Interactive CLI**: Easy-to-use command-line interface with guided prompts
- **Handles Nested JSON Structures**: Properly handles nested objects and arrays
- **Two Conversion Approaches**: Choose between flattened (single CSV) or normalized (multiple CSVs)
- **Smart Schema Detection**: Analyzes JSON structure to create consistent schemas
- **Robust Error Handling**: Comprehensive validation and detailed error messages
- **Docker Support**: Containerized deployment ready

## Installation

### Option 1: Using Poetry (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/json2csv.git
cd json2csv

# Install with Poetry
poetry install

# Activate the virtual environment
poetry shell

# Run the tool
json2csv
```

### Option 2: Using pip with Virtual Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/json2csv.git
cd json2csv

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .
```

### Option 3: Using uv

```bash
# Clone the repository
git clone https://github.com/yourusername/json2csv.git
cd json2csv

# Create a virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .
```

## Usage

### Interactive Mode

The simplest way to use the tool is in fully interactive mode:

```bash
json2csv
```

The tool will guide you through the process with prompts:
1. Explanation of conversion approaches (optional)
2. Selection of conversion mode (flattened or normalized)
3. Input JSON file path
4. Output path (file for flattened mode, directory for normalized mode)
5. Separator for nested keys (for flattened mode)

### Command-line Arguments

You can also specify options directly:

```bash
# Basic usage
json2csv --input data.json --output result.csv

# Specify mode and separator
json2csv --input data.json --output result.csv --mode flattened --separator "/"

# Normalized mode (output should be a directory)
json2csv --input data.json --output output_dir --mode normalized

# Enable verbose output
json2csv --input data.json --output result.csv --verbose

# Show version
json2csv --version

# Get help
json2csv --help
```

## Docker Usage

### Building the Docker Image

```bash
docker build -t json2csv .
```

### Running with Docker

```bash
# Run in interactive mode
docker run -it --rm -v $(pwd):/app/data json2csv

# Specify options
docker run -it --rm -v $(pwd):/app/data json2csv --input /app/data/users.json --output /app/data/output.csv
```

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/json2csv.git
cd json2csv

# Install with Poetry including dev dependencies
poetry install

# Activate the virtual environment
poetry shell
```

### Running Tests

```bash
pytest
```

## Design Decisions

### Addressing NoSQL to SQL Migration Challenges

#### 1. Schema Handling

The converter analyzes all JSON documents to create a consistent schema:
- In flattened mode, all unique keys across documents form the CSV columns
- In normalized mode, a relational schema is inferred from the JSON structure
- Objects with the same structure are grouped into related tables
- The tool automatically handles inconsistent structures by creating columns for all detected fields

#### 2. Nested Data

Two approaches are offered for handling nested data:
- **Flattened Mode**: Uses path notation with a separator (e.g., `address/city`) to represent nested fields in a single table
- **Normalized Mode**: Creates separate tables for nested objects with foreign key relationships to maintain proper database normalization

#### 3. Data Types

Type handling challenges are addressed by:
- Preserving original data types when possible
- Detecting type inconsistencies across documents
- Converting all values to strings in CSV output
- Handling `null` values by converting them to empty strings
- Supporting mixed type fields by using string representation

#### 4. Array Fields

Array handling varies by mode and content type:
- **Flattened Mode**:
  - Arrays of primitives: Indexed with numeric suffixes (e.g., `hobbies/0`, `hobbies/1`)
  - Arrays of objects: Each array item gets indexed keys (e.g., `orders/0/id`, `orders/1/total`)
- **Normalized Mode**:
  - Arrays of primitives: Stored in separate tables with foreign keys
  - Arrays of objects: Represented as separate tables with one-to-many relationships

### Implementation Decisions

1. **Choice of Click over Typer**: Click was chosen for its robustness, extensive documentation, and wide adoption. It offers a balance of simplicity and power for building interactive CLIs.

2. **Use of Poetry**: Poetry provides dependency management with lockfiles, virtual environment handling, and package building in one tool, simplifying the development workflow.

3. **Modular Architecture**: The codebase is organized into:
   - `converter.py`: Core conversion logic
   - `cli.py`: User interface
   - `utils.py`: Helper functions
   
4. **Colorful Interface**: Added color-coded output for better user experience and clarity of information.

5. **Verbose Mode**: Included detailed output option to help users understand the conversion process and troubleshoot complex JSON structures.

## License

MIT

## Author

Guni Deyo Haness