from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime, timezone
import math
import sys

PROJECT_ROOT = Path(
    "/content/D3-VITAL-X-Space-Intelligence-Platform"
)

MODULE_DIR = PROJECT_ROOT / "04_UNIFIED_DATA_LAYER"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from importlib.util import (
    spec_from_file_location,
    module_from_spec
)


def load_local_module(module_name, module_path):

    if not module_path.exists():
        raise FileNotFoundError(
            f"Required module not found: {module_path}"
        )

    spec = spec_from_file_location(
        module_name,
        module_path
    )

    if spec is None or spec.loader is None:
        raise ImportError(
            f"Could not load module: {module_path}"
        )

    module = module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


schema_module = load_local_module(
    "d3_qc_data_schema",
    MODULE_DIR / "data_schema.py"
)

validator_module = load_local_module(
    "d3_qc_data_validator",
    MODULE_DIR / "data_validator.py"
)

UnifiedDataRecord = schema_module.UnifiedDataRecord
validate_record = validator_module.validate_record


def create_qc_report(dataset_id=None):

    return {
        "qc_version": "0.1.0",
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "dataset_id": dataset_id,
        "overall_status": "NOT_EVALUATED",
        "summary": {
            "total_checks": 0,
            "passed_checks": 0,
            "warning_count": 0,
            "error_count": 0
        },
        "checks": [],
        "flags": [],
        "raw_data_modified": False,
        "scientific_validation_performed": False,
        "clinical_diagnosis_performed": False
    }


def add_qc_check(
    report,
    check_name,
    passed,
    severity="INFO",
    message="",
    details=None
):

    severity = severity.upper()

    if severity not in {"INFO", "WARNING", "ERROR"}:
        raise ValueError(
            f"Unsupported severity: {severity}"
        )

    check = {
        "check_name": check_name,
        "passed": bool(passed),
        "severity": severity,
        "message": message,
        "details": details or {}
    }

    report["checks"].append(check)
    report["summary"]["total_checks"] += 1

    if passed:
        report["summary"]["passed_checks"] += 1

    if severity == "WARNING":
        report["summary"]["warning_count"] += 1

    if severity == "ERROR":
        report["summary"]["error_count"] += 1

    if not passed or severity in {"WARNING", "ERROR"}:

        report["flags"].append({
            "check_name": check_name,
            "severity": severity,
            "message": message,
            "details": details or {}
        })


def is_nan_value(value):

    try:
        return bool(math.isnan(value))
    except (TypeError, ValueError):
        return False


def is_infinite_value(value):

    try:
        return bool(math.isinf(value))
    except (TypeError, ValueError):
        return False


def is_numeric_value(value):

    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
    )


def inspect_values(data, path="root"):

    result = {
        "total_values": 0,
        "missing_values": 0,
        "nan_values": 0,
        "infinite_values": 0,
        "negative_values": 0,
        "non_numeric_values": 0,
        "negative_value_paths": [],
        "nan_value_paths": [],
        "infinite_value_paths": []
    }

    def visit(value, current_path):

        if isinstance(value, dict):

            for key, item in value.items():
                visit(item, f"{current_path}.{key}")

            return

        if isinstance(value, (list, tuple)):

            for index, item in enumerate(value):
                visit(item, f"{current_path}[{index}]")

            return

        result["total_values"] += 1

        if value is None:

            result["missing_values"] += 1
            return

        if is_nan_value(value):

            result["nan_values"] += 1
            result["nan_value_paths"].append(current_path)
            return

        if is_infinite_value(value):

            result["infinite_values"] += 1
            result["infinite_value_paths"].append(current_path)
            return

        if is_numeric_value(value):

            if value < 0:

                result["negative_values"] += 1
                result["negative_value_paths"].append(current_path)

        else:

            result["non_numeric_values"] += 1

    visit(data, path)

    return result


def run_missing_value_check(report, inspection):

    count = inspection["missing_values"]

    add_qc_check(
        report,
        "missing_values",
        count == 0,
        "ERROR" if count > 0 else "INFO",
        (
            "Missing values detected."
            if count > 0
            else "No missing values detected."
        ),
        {"count": count}
    )


def run_nan_check(report, inspection):

    count = inspection["nan_values"]

    add_qc_check(
        report,
        "nan_values",
        count == 0,
        "ERROR" if count > 0 else "INFO",
        (
            "NaN values detected."
            if count > 0
            else "No NaN values detected."
        ),
        {
            "count": count,
            "paths": inspection["nan_value_paths"][:20]
        }
    )


def run_infinite_check(report, inspection):

    count = inspection["infinite_values"]

    add_qc_check(
        report,
        "infinite_values",
        count == 0,
        "ERROR" if count > 0 else "INFO",
        (
            "Infinite values detected."
            if count > 0
            else "No infinite values detected."
        ),
        {
            "count": count,
            "paths": inspection["infinite_value_paths"][:20]
        }
    )


def run_negative_value_check(report, inspection):

    count = inspection["negative_values"]

    add_qc_check(
        report,
        "negative_values",
        True,
        "WARNING" if count > 0 else "INFO",
        (
            "Negative values flagged for contextual review."
            if count > 0
            else "No negative numeric values detected."
        ),
        {
            "count": count,
            "policy": "FLAG_ONLY",
            "paths": inspection["negative_value_paths"][:20]
        }
    )


def run_duplicate_check(report, data):

    duplicate_count = 0
    sequence_length = 0

    if isinstance(data, (list, tuple)):

        sequence_length = len(data)

        comparable_values = []

        for value in data:

            if isinstance(value, (str, int, float, bool)):
                comparable_values.append(repr(value))

        duplicate_count = (
            len(comparable_values)
            - len(set(comparable_values))
        )

    has_duplicates = duplicate_count > 0

    add_qc_check(
        report,
        "duplicate_values",
        True,
        "WARNING" if has_duplicates else "INFO",
        (
            "Repeated values detected; contextual review required."
            if has_duplicates
            else "No duplicate scalar values detected."
        ),
        {
            "sequence_length": sequence_length,
            "duplicate_count": duplicate_count,
            "policy": "FLAG_ONLY"
        }
    )


def run_time_series_check(report, data):

    if not isinstance(data, dict):

        add_qc_check(
            report,
            "time_series_structure",
            True,
            "INFO",
            "Input is not a dictionary time-series structure.",
            {}
        )

        return

    time_values = data.get("time")
    signal_values = data.get("signal")

    if time_values is None or signal_values is None:

        add_qc_check(
            report,
            "time_series_structure",
            True,
            "INFO",
            (
                "Time/signal fields not both present; "
                "generic structure retained."
            ),
            {}
        )

        return

    lengths_match = (
        isinstance(time_values, (list, tuple))
        and isinstance(signal_values, (list, tuple))
        and len(time_values) == len(signal_values)
    )

    add_qc_check(
        report,
        "time_signal_length_match",
        lengths_match,
        "ERROR" if not lengths_match else "INFO",
        (
            "Time and signal lengths match."
            if lengths_match
            else "Time and signal lengths do not match."
        ),
        {
            "time_length": (
                len(time_values)
                if isinstance(time_values, (list, tuple))
                else None
            ),
            "signal_length": (
                len(signal_values)
                if isinstance(signal_values, (list, tuple))
                else None
            )
        }
    )

    numeric_time = all(
        is_numeric_value(value)
        for value in time_values
    ) if isinstance(time_values, (list, tuple)) else False

    if numeric_time and len(time_values) > 1:

        non_monotonic_count = sum(
            1
            for previous, current in zip(
                time_values,
                time_values[1:]
            )
            if current <= previous
        )

        is_strictly_increasing = (
            non_monotonic_count == 0
        )

        add_qc_check(
            report,
            "time_monotonicity",
            is_strictly_increasing,
            "WARNING" if not is_strictly_increasing else "INFO",
            (
                "Time values are strictly increasing."
                if is_strictly_increasing
                else "Time values are not strictly increasing."
            ),
            {
                "non_monotonic_count": non_monotonic_count
            }
        )


def run_qc(record, run_structural_validation=True):

    dataset_id = None

    if hasattr(record, "metadata"):
        dataset_id = record.metadata.dataset_id

    report = create_qc_report(dataset_id)

    if not isinstance(record, UnifiedDataRecord):

        add_qc_check(
            report,
            "record_type",
            False,
            "ERROR",
            "Input is not a UnifiedDataRecord."
        )

        report["overall_status"] = "REJECTED"
        return report

    if run_structural_validation:

        validation_result = validate_record(record)

        validation_passed = validation_result["valid"]

        add_qc_check(
            report,
            "structural_validation",
            validation_passed,
            "INFO" if validation_passed else "ERROR",
            (
                "Structural validation passed."
                if validation_passed
                else "Structural validation failed."
            ),
            {
                "errors": validation_result["errors"],
                "warnings": validation_result["warnings"]
            }
        )

    if record.data is not None:

        inspection = inspect_values(record.data)

        run_missing_value_check(report, inspection)
        run_nan_check(report, inspection)
        run_infinite_check(report, inspection)
        run_negative_value_check(report, inspection)
        run_duplicate_check(report, record.data)
        run_time_series_check(report, record.data)

    else:

        add_qc_check(
            report,
            "in_memory_payload",
            True,
            "INFO",
            (
                "No in-memory data supplied. "
                "File content inspection is not performed here."
            )
        )

    report["raw_data_modified"] = False

    if report["summary"]["error_count"] > 0:
        report["overall_status"] = "REJECTED"

    elif report["summary"]["warning_count"] > 0:
        report["overall_status"] = "PASSED_WITH_WARNINGS"

    else:
        report["overall_status"] = "PASSED"

    return report
