"""
D³ VITAL-X Time-Series Input Adapter

Converts structured time-series CSV data into UnifiedDataRecord-compatible data.
The original source file remains immutable.
No scientific processing is performed.
"""

from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import csv
import hashlib
import math


def utc_timestamp() -> str:
    """Return timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash without modifying the file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def convert_value(value: Any) -> Any:
    """Convert numeric values internally. Empty values become None."""
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    try:
        number = float(text)
        if not math.isfinite(number):
            return text
        if number.is_integer():
            return int(number)
        return number
    except (TypeError, ValueError):
        return text


def is_numeric(value: Any) -> bool:
    """Check whether a value is a finite numeric value."""
    if isinstance(value, bool):
        return False
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def generate_dataset_id(file_path: Path, raw_hash: str) -> str:
    """Generate deterministic time-series dataset ID."""
    source = f"{file_path.name}|{raw_hash}"
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
    return f"timeseries_{digest}"


def load_timeseries_csv(
    file_path: str,
    time_column: str = "time",
    signal_column: str = "signal",
    uncertainty_column: Optional[str] = None,
    encoding: str = "utf-8",
    delimiter: str = ",",
) -> Dict[str, Any]:
    """Load time-series data from CSV."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Time-series CSV not found: {path}")

    with open(path, mode="r", encoding=encoding, newline="") as file:
        reader = csv.DictReader(file, delimiter=delimiter)
        if reader.fieldnames is None:
            raise ValueError("CSV does not contain a header row.")

        columns = [str(column).strip() for column in reader.fieldnames]
        required_columns = [time_column, signal_column]
        if uncertainty_column is not None:
            required_columns.append(uncertainty_column)

        missing_columns = [
            column for column in required_columns if column not in columns
        ]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        rows = []
        for raw_row in reader:
            row = {
                column: convert_value(raw_row.get(column))
                for column in columns
            }
            rows.append(row)

    time_values = [row.get(time_column) for row in rows]
    signal_values = [row.get(signal_column) for row in rows]
    uncertainty_values = (
        [row.get(uncertainty_column) for row in rows]
        if uncertainty_column
        else None
    )

    return {
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "column_count": len(columns),
        "time": time_values,
        "signal": signal_values,
        "uncertainty": uncertainty_values,
        "time_column": time_column,
        "signal_column": signal_column,
        "uncertainty_column": uncertainty_column,
    }


def validate_timeseries_structure(
    time_values: list,
    signal_values: list,
    uncertainty_values: Optional[list] = None,
) -> Dict[str, Any]:
    """Perform structural checks only."""
    errors = []
    warnings = []

    if len(time_values) != len(signal_values):
        errors.append("Time and signal lengths do not match.")

    if uncertainty_values is not None and len(signal_values) != len(
        uncertainty_values
    ):
        errors.append("Signal and uncertainty lengths do not match.")

    invalid_time_indices = [
        i for i, v in enumerate(time_values) if not is_numeric(v)
    ]
    invalid_signal_indices = [
        i for i, v in enumerate(signal_values) if not is_numeric(v)
    ]

    if invalid_time_indices:
        errors.append(
            "Time contains missing/non-numeric values at indices:"
            f" {invalid_time_indices[:10]}"
        )
    if invalid_signal_indices:
        errors.append(
            "Signal contains missing/non-numeric values at indices:"
            f" {invalid_signal_indices[:10]}"
        )

    valid_times = [v for v in time_values if is_numeric(v)]
    duplicate_time_count = len(valid_times) - len(set(valid_times))
    if duplicate_time_count > 0:
        warnings.append(
            f"Duplicate time values detected: {duplicate_time_count}"
        )

    non_monotonic_indices = [
        i
        for i in range(1, len(valid_times))
        if valid_times[i] <= valid_times[i - 1]
    ]
    if non_monotonic_indices:
        warnings.append(
            "Time values are not strictly increasing at positions:"
            f" {non_monotonic_indices[:10]}"
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "duplicate_time_count": duplicate_time_count,
        "non_monotonic_count": len(non_monotonic_indices),
    }


def timeseries_to_unified_record(
    file_path: str,
    time_column: str = "time",
    signal_column: str = "signal",
    uncertainty_column: Optional[str] = None,
    source_name: Optional[str] = None,
    description: str = "",
    domain: Optional[Any] = None,
    license_info: str = "Not specified",
    anonymized: Optional[bool] = None,
    encoding: str = "utf-8",
    delimiter: str = ",",
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> Any:
    """Convert time-series CSV into UnifiedDataRecord structure dictionary/object."""
    path = Path(file_path)
    if source_name is None:
        source_name = path.name

    raw_hash = calculate_sha256(path)
    dataset_id = generate_dataset_id(path, raw_hash)

    loaded = load_timeseries_csv(
        file_path=str(path),
        time_column=time_column,
        signal_column=signal_column,
        uncertainty_column=uncertainty_column,
        encoding=encoding,
        delimiter=delimiter,
    )

    structure_report = validate_timeseries_structure(
        time_values=loaded["time"],
        signal_values=loaded["signal"],
        uncertainty_values=loaded["uncertainty"],
    )

    metadata_extra = {
        "adapter": "timeseries_adapter",
        "adapter_version": "1.0.0",
        "time_column": time_column,
        "signal_column": signal_column,
        "uncertainty_column": uncertainty_column,
        "row_count": loaded["row_count"],
        "column_count": loaded["column_count"],
        "columns": loaded["columns"],
        "structure_report": structure_report,
        "raw_sha256": raw_hash,
        "raw_file_size_bytes": path.stat().st_size,
        "scientific_processing_performed": False,
        "created_at": utc_timestamp(),
    }

    if extra_metadata is not None:
        metadata_extra.update(extra_metadata)

    return {
        "dataset_id": dataset_id,
        "source_name": source_name,
        "file_path": str(path),
        "raw_data_hash": raw_hash,
        "raw_data_immutable": True,
        "data": loaded,
        "metadata": metadata_extra,
        "validation": structure_report,
    }


def summarize_timeseries_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a machine-readable summary of the record."""
    return {
        "dataset_id": record.get("dataset_id"),
        "source_name": record.get("source_name"),
        "row_count": record.get("data", {}).get("row_count"),
        "structure_valid": record.get("validation", {}).get("valid"),
        "raw_sha256": record.get("raw_data_hash"),
        "raw_data_immutable": record.get("raw_data_immutable"),
        "generated_at": utc_timestamp(),
    }
