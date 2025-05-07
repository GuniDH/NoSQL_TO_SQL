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

        click.echo("Conversion Options:")
        click.secho("  • flattened  → single CSV with path-style columns & indexed arrays", fg="green")
        click.secho("  • normalized → multiple CSV files with root.csv, foreign keys, surrogate IDs", fg="green")
        click.echo(r"""
        ──────────────────────────  APPROACH OVERVIEW  ──────────────────────────
        Flattened  → 1 CSV (default approach from the project's instructiosn)
        • Every JSON field—no matter how deeply nested—turns into a column.
            address/street, address/city, prefs/alerts/email, …
        • Arrays become numbered columns: tags/0, tags/1, …
        • Simple to open in Excel or import into BI tools without joins.
        • Drawbacks: very wide files, repeated data for arrays of objects, and you
            lose explicit parent/child relationships.

        Normalized → many CSVs
        • root.csv holds the top‑level fields plus a generated root_id.
        • Each nested object/array is stored in its own table (addresses.csv,
            orders.csv, tags.csv, …).
            – Every table gets a surrogate primary key named {singular}_id.
            – A foreign‑key column points **to its immediate parent**, mirroring the
                JSON hierarchy - nested FKs (root_id → addresses.csv; address_id → streets.csv, etc.).
        • Eliminates duplication and preserves true relationships—ideal for loading
            into PostgreSQL/MySQL, doing JOINs, and enforcing referential integrity.
        • Drawbacks: you’ll manage multiple files and need SQL joins to reconstruct
            the full document.

        Tip → Pick F if you want a quick spreadsheet‑friendly snapshot.
            Pick N if you plan to load into a relational DB or do normalized analytics.
            Press <Enter> to accept the default (Flattened).
        ─────────────────────────────────────────────────────────────────────────
        """)
        # Prompt for mode each iteration
        click.echo("Select conversion mode:")
        choice = click.prompt(
            "Flattened or Normalized", 
            type=click.Choice(["F","N"], case_sensitive=False), 
            default="F"
        )
        mode = "flattened" if choice.upper() == "F" else "normalized"
        click.echo(f"Mode set to: {mode}\n")
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
