import os
from pathlib import Path
import click

def safe_path(raw: str, must_exist: bool, is_dir: bool):
    """
    Strip whitespace, resolve '..', ensure correct type,
    create if needed (when must_exist=False).
    """
    p = Path(raw.strip()).expanduser().resolve()
    if must_exist:
        if not p.exists():
            click.secho(f"Path not found: {p}", fg="red", err=True)
            return None
        if is_dir and not p.is_dir():
            click.secho(f"Not a directory: {p}", fg="red", err=True)
            return None
        if not is_dir and not p.is_file():
            click.secho(f"Not a file: {p}", fg="red", err=True)
            return None
    else:
        # create parent(s)
        p_dir = p if is_dir else p.parent
        os.makedirs(p_dir, exist_ok=True)
    return p
