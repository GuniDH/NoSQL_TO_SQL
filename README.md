# JSON → CSV Converter - Guni Deyo Haness

A fully‑featured Python CLI for migrating **NoSQL‑style JSON documents** to **SQL‑style CSV files.** 
Built with **Click** (for rich interactive prompts) and **pluralizer** (for consistent singular/plural naming).

It supports the **flattened** approach - the default option from the project instructions that require a single csv output file.
But it also supports a bonus option - fully **normalized** export for relational databases with multiple csv output files which is optimal.

## Conversion modes

| Mode           | Output type        | Handling of nested data                                                                                                                                                                                                                                                                                                |
| -------------- | ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Flattened**  | Single CSV file    | Nested keys joined with slashes (`address/street`, `prefs/alerts/email`). Arrays expanded as indexed columns (`tags/0`, `tags/1`, …).                                                                                                                                                                                  |
| **Normalized** | Multiple CSV files | `root.csv` plus one table per nested object or array. Every generated table gets a surrogate **primary key** named `{singular}_id`, and a **foreign‑key column** that points **to its immediate parent table** (nested/indirect FK). This avoids guessing global relationships and cleanly mirrors the JSON hierarchy. |


### Why we use nested (indirect) foreign keys in the bonus normalized approach:

| Aspect | **Nested FK** (child → immediate parent) | **Direct FK** (child → root) |
|--------|------------------------------------------|------------------------------|
| **Normal forms** | Fully satisfies 2NF/3NF because every non‑key column depends only on its table’s PK. | Skips a logical level; still valid but can introduce partial‑dependency concerns. |
| **Future‑proofing** | If a single object later becomes an array, you just add rows—no schema migration. | Requires adding a new table and rewriting FKs. |
| **Query flexibility** | Can traverse the hierarchy or flatten with joins as needed. | Simpler for root‑level reports only. |
| **Join cost** | One extra indexed join (typically a few ms). | Slightly faster—one join fewer—but negligible with indexes. |

Nested FKs mirror the JSON structure, preserve normal‑form integrity, and adapt to future changes, while the extra join overhead is minimal.

---

## 1 · Installation

```bash
# clone and enter the repo
git clone https://github.com/your‑org/json2csv.git
cd json2csv
```

### 1.1 Poetry (recommended)

```bash
# install dependencies in an isolated virtual‑env
poetry install

# optional: activate that environment in a specific path (Poetry normally stores venvs in a cache)
poetry env activate $(poetry env info --path)
```

### 1.2 pip + venv

| OS                     | Commands                                                                |
| ---------------------- | ----------------------------------------------------------------------- |
| **macOS/Linux**        | `python3 -m venv .venv && source .venv/bin/activate && pip install .`   |
| **Windows PowerShell** | `python -m venv .venv ; .\.venv\Scripts\Activate.ps1 ; pip install .`   |
| **Windows CMD**        | `python -m venv .venv && .\.venv\Scripts\activate.bat && pip install .` |

### 1.3 uv (fast installer)

| OS                     | Commands                                                                |
| ---------------------- | ----------------------------------------------------------------------- |
| **macOS/Linux**        | `python3 -m venv .venv && source .venv/bin/activate`   |
| **Windows PowerShell** | `python -m venv .venv ; .\.venv\Scripts\Activate.ps1`   |
| **Windows CMD**        | `python -m venv .venv && .\.venv\Scripts\activate.bat` |


```bash
 pip install uv                                       # install uv itself
 uv pip install --requirements requirements.txt       # install runtime + pytest
 uv pip install --editable .                          # install json2csv package
```

## 1.4 docker
```bash
docker build -t json2csv .
```

---

## 2 · Running the CLI (you have --help, --verbose flags)

```bash
poetry run json2csv # poetry
json2csv            # uv or pip (both venv)
docker run --rm -it -v "${PWD}:/app" -w /app json2csv # docker
```

Interactive flow:

1. Choose **F**lattened (default) or **N**ormalized.
2. Provide an **input JSON path** (validated, must exist).
3. Provide an **output path**:

   * Flattened: file path for a single CSV (parent directory auto‑created).
   * Normalized: directory for multiple CSVs (created if missing).
4. Decide whether to convert another file or exit.

---

## 3 · Testing (-q flag optional)

```bash
poetry run pytest      # poetry
pytest                 # uv or pip (both venv)
docker run --rm -it -v "${PWD}:/app" -w /app --entrypoint pytest json2csv -q # docker
```

The test suite focuses on **data‑transformation logic**:

* Deeply nested objects and arrays.
* Surrogate primary‑key generation and foreign‑key integrity.
* `utils.safe_path` sanitisation and directory creation to prevent directory traversal attack in case this app scales to an app server (i would personally develop it on fastapi).

---

## 4 · NoSQL → SQL Migration Challenges & Solutions

| Challenge           | Why it’s hard                                   | Flattened approach                                                       | Normalized approach                                                                                 |
| ------------------- | ----------------------------------------------- | ------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------- |
| **Schema Handling** | JSON is schema‑less; keys vary by document.     | Pre‑scan to union all key paths; absent keys → empty CSV cells.          | Tables are created when first encountered; column headers grow to include any later‑seen fields.    |
| **Nested Data**     | SQL tables are flat.                            | Keys collapsed with `/`; arrays expanded as indexed columns.             | Each object/array becomes its own table. Child tables carry a foreign key to the parent table.      |
| **Data Types**      | Same key can hold different types.              | Values written as‑is (CSV stores text). Down‑stream ETL casts as needed. | Same: CSV preserves original text; coercion happens on SQL import.                                  |
| **Array Fields**    | Variable‑length arrays don’t fit fixed columns. | Indexed columns (`tags/0`, `tags/1`, …).                                 | Arrays of primitives → `{plural}.csv` with `(id, root_id, value)`. Arrays of objects → full tables. |


### Extra Design Decisions

* **Lockfiles**: Poetry generates `poetry.lock`; uv can create `uv.lock` for reproducible builds.
* **Naming**: table names plural; primary keys `{singular}_id`; Pointing to parent with forign key (nested FKs).
* **Click vs. Typer**: Typer is a wrapper on top of Click; using it would add an extra irrelaven layer which auto‑generates flags from function signatures but limits low‑level styling and prompt control. We need Click’s direct control for custom colors and looping, so sticking with Click keeps the stack lean.
* **Path Security**: `utils.safe_path` strips whitespace, expands `~`, resolves `..`, validates existing paths, and auto‑creates output directories to prevent directory‑traversal exploits - VERY important if this project scales to a server application (i would personally develop it on fastapi).

---

## 5 · End‑to‑end example

### 5.1  Input JSON

```json
[
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
      "newsletter": true,
      "notifications": { "email": true, "sms": false }
    },
    "hobbies": ["reading", "swimming", "coding"],
    "orders": [
      { "id": 101, "total": 50.00, "date": "2024‑01‑15" },
      { "id": 102, "total": 75.50, "date": "2024‑02‑01" }
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
      "state": "NY"
    },
    "preferences": { "newsletter": false },
    "hobbies": ["painting"],
    "orders": []
  }
]

```
### 5.2  Flattened output (`flattened.csv`)

| id | name | email | age | address/street | address/city | address/state | address/zip | preferences/newsletter | preferences/notifications/email | preferences/notifications/sms | hobbies/0 | hobbies/1 | hobbies/2 | hobbies/3 | orders/0/id | orders/0/total | orders/0/date | orders/1/id | orders/1/total | orders/1/date |
|----|------|-------|-----|----------------|--------------|---------------|-------------|-----------------------|---------------------------------|-------------------------------|-----------|-----------|-----------|-----------|-------------|----------------|---------------|-------------|----------------|---------------|
| 1 | John Doe | john@example.com | 30 | 123 Main St | Boston | MA | 02118 | true | true | false | reading | swimming | coding |   | 101 | 50.00 | 2024‑01‑15 | 102 | 75.50 | 2024‑02‑01 |
| 2 | Jane Smith | jane@example.com | 25 | 456 Oak Ave | New York | NY |   | false |   |   | painting |   |   |   |   |   |   |   |   |   |

---

### 5.3  Normalized output – six CSV tables

#### root.csv
| user_id | name | email | age |
|---------|------|-------|-----|
| 1 | John Doe | john@example.com | 30 |
| 2 | Jane Smith | jane@example.com | 25 |

#### addresses.csv
| address_id | user_id | street | city | state | zip |
|------------|---------|--------|------|-------|-----|
| 1 | 1 | 123 Main St | Boston | MA | 02118 |
| 2 | 2 | 456 Oak Ave | New York | NY | *(null)* |

#### preferences.csv
| preference_id | user_id | newsletter |
|---------------|---------|------------|
| 1 | 1 | true |
| 2 | 2 | false |

#### notifications.csv
| notification_id | preference_id | email | sms |
|-----------------|---------------|-------|-----|
| 1 | 1 | true | false |

#### hobbies.csv
| hobby_id | user_id | hobby |
|----------|---------|-------|
| 1 | 1 | reading |
| 2 | 1 | swimming |
| 3 | 1 | coding |
| 4 | 2 | painting |

#### orders.csv
| order_id | user_id | total | date |
|----------|---------|-------|------------|
| 101 | 1 | 50.00 | 2024‑01‑15 |
| 102 | 1 | 75.50 | 2024‑02‑01 |


## Author

Guni Deyo Haness
