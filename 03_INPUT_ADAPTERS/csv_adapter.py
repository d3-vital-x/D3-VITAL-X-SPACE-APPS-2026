"""
D³ VITAL-X SPACE INTELLIGENCE PLATFORM
MODULE 08: CSV INPUT ADAPTER
"""

from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import csv
import hashlib
import json
import math

def utc_timestamp() -> str:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of the original CSV file in binary mode."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def safe_column_name(column_name: Any) -> str:
    """Convert CSV header into a safe string."""
    if column_name is None:
        return ""
    return str(column_name).strip()

def detect_numeric(value: Any) -> bool:
    """Determine whether a value can be interpreted as numeric."""
    if value is None:
        return False
    text = str(value).strip()
    if text == "":
        return False
    try:
        number = float(text)
        return math.isfinite(number)
    except (TypeError, ValueError):
        return False

def convert_value(value: Any) -> Any:
    """Convert numeric CSV values to int/float where possible while preserving missing values."""
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    if not detect_numeric(text):
        return text
    try:
        number = float(text)
        if number.is_integer():
            return int(number)
        return number
    except (TypeError, ValueError):
        return text

def generate_dataset_id(file_path: Path, raw_hash: str) -> str:
    """Generate a deterministic dataset identifier."""
    identifier_source = f"{file_path.name}|{raw_hash}"
    digest = hashlib.sha256(identifier_source.encode("utf-8")).hexdigest()[:16]
    return f"csv_{digest}"

def inspect_csv(file_path: str, encoding: str = "utf-8", delimiter: str = ",") -> Dict[str, Any]:
    """Inspect CSV structure without creating a UnifiedDataRecord."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    with open(path, mode="r", encoding=encoding, newline="") as file:
        reader = csv.DictReader(file, delimiter=delimiter)
        raw_fieldnames = reader.fieldnames or []
        fieldnames = [safe_column_name(name) for name in raw_fieldnames]
        duplicate_columns = [name for name in set(fieldnames) if fieldnames.count(name) > 1]

        row_count = 0
        missing_values = {column: 0 for column in fieldnames}
        non_empty_values = {column: [] for column in fieldnames}

        for row in reader:
            row_count += 1
            for column in fieldnames:
                value = row.get(column)
                if value is None or str(value).strip() == "":
                    missing_values[column] += 1
                else:
                    non_empty_values[column].append(value)

    numeric_columns = []
    text_columns = []

    for column in fieldnames:
        values = non_empty_values[column]
        if values and all(detect_numeric(value) for value in values):
            numeric_columns.append(column)
        else:
            text_columns.append(column)

    return {
        "file_name": path.name,
        "file_path": str(path),
        "row_count": row_count,
        "column_count": len(fieldnames),
        "columns": fieldnames,
        "duplicate_columns": duplicate_columns,
        "missing_values": missing_values,
        "numeric_columns": numeric_columns,
        "text_columns": text_columns,
        "encoding": encoding,
        "delimiter": delimiter,
        "inspected_at": utc_timestamp()
    }

def load_csv_data(file_path: str, encoding: str = "utf-8", delimiter: str = ",") -> Dict[str, Any]:
    """Load CSV data into an internal dictionary representation."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    with open(path, mode="r", encoding=encoding, newline="") as file:
        reader = csv.DictReader(file, delimiter=delimiter)
        if reader.fieldnames is None:
            raise ValueError("CSV file does not contain a header row.")

        columns = [safe_column_name(column) for column in reader.fieldnames]
        rows = []

        for raw_row in reader:
            converted_row = {column: convert_value(raw_row.get(column)) for column in columns}
            rows.append(converted_row)

    return {
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "column_count": len(columns)
    }
