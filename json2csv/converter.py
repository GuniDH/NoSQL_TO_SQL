import json
import csv
from pathlib import Path
from collections import OrderedDict
from pluralizer import Pluralizer

# Initialize pluralizer once
pluralizer = Pluralizer()

def flatten_to_csv(json_path: str, csv_path: str, verbose: bool=False):
    data = json.loads(Path(json_path).read_text())
    if not isinstance(data, list):
        raise ValueError("Top-level JSON must be an array of objects.")

    rows = []
    columns = []  # preserve insertion order of columns

    for rec in data:
        row = OrderedDict()
        def _flatten(obj, prefix=""):
            for k, v in obj.items():
                key = f"{prefix}{k}" if not prefix else f"{prefix}/{k}"
                if isinstance(v, dict):
                    _flatten(v, key)
                elif isinstance(v, list):
                    for i, item in enumerate(v):
                        subkey = f"{key}/{i}"
                        if isinstance(item, dict):
                            _flatten(item, subkey)
                        else:
                            # primitives: preserve original type
                            row[subkey] = item
                else:
                    # scalars: preserve original type (bool,int,str,etc.)
                    row[key] = v
        _flatten(rec)

        for col in row.keys():
            if col not in columns:
                columns.append(col)
        rows.append(row)

    # ensure output directory exists
    Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
    # write CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    if verbose:
        print(f"[flatten] wrote {len(rows)} rows with {len(columns)} columns")

        
def normalize_to_csv(json_path: str, out_dir: str, verbose: bool=False):
    data = json.loads(Path(json_path).read_text())
    if not isinstance(data, list):
        raise ValueError("Top-level JSON must be an array of objects.")

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    tables = {}   # table_name -> list of OrderedDict rows
    counters = {} # table_name -> auto-increment counter

    def _new_id(table: str) -> int:
        counters.setdefault(table, 0)
        counters[table] += 1
        return counters[table]

    def _process(obj: dict, table: str, parent_ref=None):
        tables.setdefault(table, [])
        # determine PK field name
        if table == 'root':
            pk_field = 'root_id'
            pk_val = _new_id('root')
        else:
            pk_field = f"{pluralizer.singular(table)}_id"
            # use JSON 'id' if available, else generate
            if 'id' in obj and not isinstance(obj['id'], (dict, list)):
                pk_val = obj['id']
            else:
                pk_val = _new_id(table)
        # start row
        row = OrderedDict([(pk_field, pk_val)])
        # attach FK to parent
        if parent_ref:
            _, fk_field, parent_id = parent_ref
            row[fk_field] = parent_id

        # separate scalars and nested
        nested = []
        for key, val in obj.items():
            if key == 'id':
                continue
            if isinstance(val, (dict, list)):
                nested.append((key, val))
            else:
                row[key] = val
        tables[table].append(row)

        # recurse nested
        for key, val in nested:
            child_table = pluralizer.plural(key)
            fk_field = 'root_id' if table == 'root' else pk_field
            if isinstance(val, dict):
                if val:
                    _process(val, child_table, (table, fk_field, pk_val))
            else:
                # array of primitives
                if all(not isinstance(i, (dict, list)) for i in val):
                    for item in val:
                        child_pk = f"{pluralizer.singular(child_table)}_id"
                        # if JSON object has 'id', use it
                        if isinstance(item, dict) and 'id' in item:
                            child_val = item['id']
                        else:
                            child_val = _new_id(child_table)
                        child_row = OrderedDict([
                            (child_pk, child_val),
                            (fk_field, pk_val),
                            (pluralizer.singular(child_table), item if not isinstance(item, dict) else item.get(pluralizer.singular(child_table)))
                        ])
                        tables.setdefault(child_table, []).append(child_row)
                else:
                    for item in val:
                        _process(item, child_table, (table, fk_field, pk_val))

    # process records
    for record in data:
        _process(record, 'root', None)

    # write CSVs
    for tbl, rows in tables.items():
        file_path = out_path / f"{tbl}.csv"
        columns = []
        for r in rows:
            for c in r.keys():
                if c not in columns:
                    columns.append(c)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
        if verbose:
            print(f"[normalize] wrote {len(rows)} rows to {tbl}.csv")
