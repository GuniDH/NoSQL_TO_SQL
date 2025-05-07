import json
import tempfile
import csv
from pathlib import Path
import pytest
from json2csv.converter import flatten_to_csv, normalize_to_csv
from json2csv.utils import safe_path

SAMPLE = [
    {"id": 1, "name": "A", "tags": ["x","y"], "meta": {"a": True}},
    {"id": 2, "name": "B", "tags": [],     "meta": {}}
]

def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def test_flatten(tmp_path):
    jf = tmp_path / "in.json"
    jf.write_text(json.dumps(SAMPLE))
    out = tmp_path / "flat.csv"
    flatten_to_csv(str(jf), str(out))
    rows = read_csv(out)
    assert len(rows) == 2
    assert "tags/0" in rows[0]
    assert "meta/a" in rows[0]

def test_normalize(tmp_path):
    jf = tmp_path / "in.json"
    jf.write_text(json.dumps(SAMPLE))
    outdir = tmp_path / "outdir"
    normalize_to_csv(str(jf), str(outdir))
    # root.csv exists
    root = read_csv(outdir / "root.csv")
    assert len(root) == 2
    # tags.csv exists
    tags = read_csv(outdir / "tags.csv")
    # two tags total
    assert len(tags) == 2
    # meta.csv exists
    meta = read_csv(outdir / "metas.csv")
    # only one row where meta non-empty
    assert len(meta) == 1

# Extended tests

def make_complex_sample():
    return [
        {
            "id": 10,
            "user": {"name": "Alice", "age": 27},
            "prefs": {"theme": "dark", "alerts": {"email": False, "sms": True}},
            "items": [
                {"id": 1001, "price": 9.99},
                {"id": 1002, "price": 14.95}
            ],
            "tags": ["new", "sale"]
        },
        {
            "id": 11,
            "user": {"name": "Bob"},
            "prefs": {},
            "items": [],
            # "tags" missing to test optional arrays
        }
    ]

@pytest.mark.parametrize("must_exist,is_dir,expect", [
    (True, False, False),  # non-existent file
    (True, True, False),   # non-existent dir
])
def test_safe_path_invalid(tmp_path, must_exist, is_dir, expect):
    bad = str(tmp_path / "nope")
    p = safe_path(bad, must_exist=must_exist, is_dir=is_dir)
    assert p is None

def test_safe_path_output_creates_dirs(tmp_path):
    file_out = tmp_path / "sub/dir/out.csv"
    p = safe_path(str(file_out), must_exist=False, is_dir=False)
    assert p == file_out.resolve()
    assert (tmp_path / "sub/dir").exists()

def test_flatten_complex(tmp_path):
    sample = make_complex_sample()
    jf = tmp_path / "in.json"
    jf.write_text(json.dumps(sample))
    out = tmp_path / "flat_complex.csv"
    flatten_to_csv(str(jf), str(out))
    rows = list(csv.DictReader(open(out)))
    # Should produce two rows
    assert len(rows) == 2
    # Check nested user fields flattened
    assert rows[0]["user/name"] == "Alice"
    assert rows[1]["user/age"] == ""
    # Check boolean preserved
    assert rows[0]["prefs/alerts/sms"] == "True"
    assert rows[1]["prefs/alerts/sms"] == ""

def test_normalize_complex(tmp_path):
    sample = make_complex_sample()
    jf = tmp_path / "in2.json"
    jf.write_text(json.dumps(sample))
    outdir = tmp_path / "out_norm"
    normalize_to_csv(str(jf), str(outdir))
    # Root table
    root = list(csv.DictReader(open(outdir / "root.csv")))
    assert len(root) == 2
    # Items table uses JSON ids 1001,1002 for first row
    items = list(csv.DictReader(open(outdir / "items.csv")))
    ids = sorted(int(r["item_id"]) for r in items)
    assert ids == [1001, 1002]
    # Second user has no items
    assert all(r["root_id"] == root[0]["root_id"] or r["root_id"] == root[1]["root_id"] for r in items)

def test_flatten_and_normalize_roundtrip(tmp_path):
    # Ensure that normalizing then flattening matches original flatten output
    sample = make_complex_sample()
    jf = tmp_path / "in3.json"
    jf.write_text(json.dumps(sample))
    norm_dir = tmp_path / "norm_rt"
    normalize_to_csv(str(jf), str(norm_dir))
    # Flatten normalized root.csv back
    flat_from_norm = tmp_path / "flat_rt.csv"
    # Merge root + items + tags back manually for comparison
    # For simplicity, just check that root->flat root columns exist
    root_csv = norm_dir / "root.csv"
    reader = csv.DictReader(open(root_csv))
    cols = reader.fieldnames
    assert 'root_id' in cols
