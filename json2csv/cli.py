"""
Command-line interface for the JSON to CSV converter.
"""
import os
import json
from pathlib import Path
from typing import Optional

import click

from json2csv.converter import convert_json_to_csv, read_json
from json2csv.utils import validate_json_path, detect_json_structure

# Get version from package
from json2csv import __version__


FLATTENED_EXPLANATION = """
Flattened approach:
This converts your JSON to a single CSV file with nested structures flattened using path notation.
For example, an object like {"address": {"city": "Boston"}} becomes a column "address/city" with value "Boston".
Arrays are also flattened with indexed notation.
This is useful when you want all data in a single table.
"""

NORMALIZED_EXPLANATION = """
Normalized approach:
This converts your JSON to multiple CSV files representing a relational database structure.
Each nested object or array becomes its own CSV file with proper primary/foreign key relationships.
For example, your data becomes tables like "root.csv", "address.csv", "orders.csv", etc.
This is useful when preserving proper database normalization is important.
"""


@click.command(help="Convert JSON data to CSV format. If no options are provided, the tool runs in interactive mode.")
@click.version_option(version=__version__)
@click.option(
    "--input", "-i", "input_path", 
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path to the input JSON file"
)
@click.option(
    "--output", "-o", "output_path", 
    type=click.Path(file_okay=True, dir_okay=True, writable=True),
    help="Path to the output CSV file or directory"
)
@click.option(
    "--mode", "-m", 
    type=click.Choice(["flattened", "normalized"]),
    help="Mode of conversion: 'flattened' (single CSV) or 'normalized' (multiple CSVs)"
)
@click.option(
    "--separator", "-s", 
    default="/",
    help="Separator for nested keys in flattened mode"
)
@click.option(
    "--verbose", "-v", is_flag=True,
    help="Enable detailed output for debugging"
)
def main(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None,
    mode: Optional[str] = None,
    separator: str = "/",
    verbose: bool = False
) -> None:
    """
    Convert JSON data to CSV format.
    
    If called without options, the tool will run in interactive mode, prompting for all needed information.
    """
    # Welcome message with colorful output
    click.secho("JSON to CSV Converter", fg="blue", bold=True)
    
    # If no arguments provided, run in fully interactive mode
    if input_path is None and output_path is None and mode is None:
        click.secho("Running in interactive mode...", fg="cyan")
        
        # Ask for conversion mode with explanation
        if click.confirm("Would you like an explanation of the available conversion approaches?", default=True):
            click.secho(FLATTENED_EXPLANATION, fg="green")
            click.secho(NORMALIZED_EXPLANATION, fg="green")
        
        mode_options = ["flattened", "normalized"]
        mode = click.prompt(
            click.style("Which conversion approach would you like to use?", fg="cyan"),
            type=click.Choice(mode_options),
            default="flattened"
        )
        
        # Ask for input file path
        while True:
            input_path = click.prompt(click.style("Enter the input JSON file path", fg="cyan"), type=str)
            if validate_json_path(input_path):
                break
            click.secho(f"Error: The file '{input_path}' does not exist or is not valid JSON.", fg="red")
        
        # Ask for output path based on the chosen mode
        if mode == "flattened":
            output_path = click.prompt(click.style("Enter the output CSV file path", fg="cyan"), type=str)
        else:  # normalized
            output_path = click.prompt(click.style("Enter the output directory for CSV files", fg="cyan"), type=str)
        
        # Ask for separator only in flattened mode
        if mode == "flattened":
            separator = click.prompt(
                click.style("Enter the separator for nested keys", fg="cyan"), 
                default="/", 
                type=str
            )
    
    # If mode not provided but other args are, prompt just for mode
    elif mode is None:
        if click.confirm("Would you like an explanation of the available conversion approaches?", default=True):
            click.secho(FLATTENED_EXPLANATION, fg="green")
            click.secho(NORMALIZED_EXPLANATION, fg="green")
        
        mode_options = ["flattened", "normalized"]
        mode = click.prompt(
            click.style("Which conversion approach would you like to use?", fg="cyan"),
            type=click.Choice(mode_options),
            default="flattened"
        )
    
    # If input path not provided, prompt for it
    if input_path is None:
        while True:
            input_path = click.prompt(click.style("Enter the input JSON file path", fg="cyan"), type=str)
            if validate_json_path(input_path):
                break
            click.secho(f"Error: The file '{input_path}' does not exist or is not valid JSON.", fg="red")
    
    # If output path not provided, prompt for it
    if output_path is None:
        if mode == "flattened":
            output_path = click.prompt(click.style("Enter the output CSV file path", fg="cyan"), type=str)
        else:  # normalized
            output_path = click.prompt(click.style("Enter the output directory for CSV files", fg="cyan"), type=str)
    
    try:
        # Verbose output about the JSON structure if requested
        if verbose:
            click.secho("Analyzing JSON structure...", fg="blue")
            json_data = read_json(input_path)
            click.echo(f"Found {len(json_data)} records in the JSON file")
            
            # Detect and display structure information
            structure = detect_json_structure(json_data)
            click.echo("Detected structure:")
            for key, info in structure.items():
                if "type" in info:
                    types = ", ".join(info["type"])
                    click.echo(f"  - {key}: {types}")
                    if info.get("nested"):
                        click.echo("    (has nested structure)")
            
            click.secho(f"Using conversion mode: {mode}", fg="blue")
            if mode == "flattened":
                click.echo(f"Using separator: '{separator}' for nested keys")
        
        # Ensure the output directory exists for normalized mode
        if mode == "normalized":
            output_dir = output_path
            if Path(output_dir).suffix:  # If output_path has an extension
                output_dir = str(Path(output_path).parent / Path(output_path).stem)
            os.makedirs(output_dir, exist_ok=True)
            
            if verbose:
                click.echo(f"Created output directory: {output_dir}")
        elif mode == "flattened":
            # Ensure the output directory exists for the single CSV file
            output_dir = os.path.dirname(os.path.abspath(output_path))
            if output_dir:  # Only create if there's a directory component
                os.makedirs(output_dir, exist_ok=True)
                if verbose:
                    click.echo(f"Ensured output directory exists: {output_dir}")
        
        # Conversion progress message
        click.secho("Converting JSON to CSV...", fg="blue")
        
        # Convert the JSON to CSV
        convert_json_to_csv(input_path, output_path, mode, separator)
        
        # Success message
        if mode == "flattened":
            click.secho(f"✅ Successfully converted {input_path} to {output_path}", fg="green", bold=True)
        else:
            output_dir = output_path
            if Path(output_dir).suffix:  # If output_path has an extension
                output_dir = str(Path(output_path).parent / Path(output_path).stem)
            click.secho(f"✅ Successfully converted {input_path} to multiple CSV files in {output_dir}", fg="green", bold=True)
            
    except ValueError as e:
        # Handle security errors
        if "Security error" in str(e):
            click.secho(f"❌ {str(e)}", fg="red", bold=True)
        else:
            click.secho(f"❌ Error: {str(e)}", fg="red", bold=True)
            if verbose:
                # In verbose mode, show the full exception traceback
                click.echo("\nDetailed error information:")
                import traceback
                click.echo(traceback.format_exc())
        return
    except Exception as e:
        click.secho(f"❌ Error: {str(e)}", fg="red", bold=True)
        if verbose:
            # In verbose mode, show the full exception traceback
            click.echo("\nDetailed error information:")
            import traceback
            click.echo(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()