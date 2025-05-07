import sys
import click
from pathlib import Path
from .utils import safe_path
from .converter import flatten_to_csv, normalize_to_csv

VERSION = "0.1.0"

@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=VERSION, prog_name="json2csv")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output.")
def main(verbose):
    """
    JSON → CSV Converter Interactive CLI

    Each iteration, choose conversion mode:
    (F)lattened → single CSV file
    (N)ormalized → multiple CSV files
    """
    click.secho("\nJSON → CSV Converter", fg="cyan", bold=True)

    while True:
        # Prompt for mode each iteration
        click.echo("Select conversion mode:")
        choice = click.prompt(
            "Flattened or Normalized (Enter either F or N to choose or click enter to stay with default - F)", 
            type=click.Choice(["F","N"], case_sensitive=False), 
            default="F"
        )
        mode = "flattened" if choice.upper() == "F" else "normalized"
        click.echo(f"Mode set to: {mode}\n")

        click.echo("Mode details:")
        click.secho("  • flattened  → single CSV with path-style columns & indexed arrays", fg="green")
        click.secho("  • normalized → multiple CSV files with root.csv, foreign keys, surrogate IDs", fg="green")
        click.echo()

        # Prompt for input JSON
        raw_in = click.prompt("Enter path to input JSON file", type=str)
        in_path = safe_path(raw_in, must_exist=True, is_dir=False)
        if not in_path:
            continue

        # Perform conversion based on mode
        if mode == "flattened":
            raw_out = click.prompt("Enter path for output CSV file", type=str)
            out_path = safe_path(raw_out, must_exist=False, is_dir=False)
            try:
                flatten_to_csv(in_path, out_path, verbose=verbose)
                click.secho(f"Flattened CSV written to {out_path}", fg="blue")
            except Exception as e:
                click.secho(f"Error: {e}", fg="red", err=True)
        else:
            raw_outdir = click.prompt("Enter path for output CSV directory", type=str)
            out_dir = safe_path(raw_outdir, must_exist=False, is_dir=True)
            try:
                normalize_to_csv(in_path, out_dir, verbose=verbose)
                click.secho(f"Normalized CSVs written under {out_dir}", fg="blue")
            except Exception as e:
                click.secho(f"Error: {e}", fg="red", err=True)

        # Continue or exit
        if not click.confirm("Convert another JSON file?", default=True):
            click.secho("Goodbye!", fg="cyan")
            sys.exit(0)

if __name__ == "__main__":
    main()
