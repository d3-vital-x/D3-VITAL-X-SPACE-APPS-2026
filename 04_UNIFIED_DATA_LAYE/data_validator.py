
from pathlib import Path
from typing import Any, Dict, Optional
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
    "d3_data_schema",
    MODULE_DIR / "data_schema.py"
)

registry_module = load_local_module(
    "d3_format_registry",
    MODULE_DIR / "format_registry.py"
)

UnifiedDataRecord = schema_module.UnifiedDataRecord

detect_format = registry_module.detect_format

DEFAULT_MAX_FILE_SIZE_MB = 2048

SUPPORTED_INPUT_TYPES = {
    "CSV",
    "IMAGE",
    "TIME_SERIES",
    "DICOM",
    "VIDEO",
    "NASA",
    "UNKNOWN",
}


def create_validation_result():

    return {
        "valid": True,
        "errors": [],
        "warnings": [],
        "checks": {},
        "status": "NOT_VALIDATED"
    }


def add_error(result, message):

    result["errors"].append(message)
    result["valid"] = False


def add_warning(result, message):

    result["warnings"].append(message)


def add_check(result, name, passed, details=None):

    result["checks"][name] = {
        "passed": bool(passed),
        "details": details or ""
    }


def validate_record_type(record, result):

    is_valid = isinstance(
        record,
        UnifiedDataRecord
    )

    add_check(
        result,
        "record_type",
        is_valid,
        "UnifiedDataRecord instance required."
    )

    if not is_valid:
        add_error(
            result,
            "Input is not a UnifiedDataRecord instance."
        )

    return is_valid


def validate_metadata(record, result):

    metadata = record.metadata

    required_fields = {
        "dataset_id": metadata.dataset_id,
        "source_name": metadata.source_name,
        "source_type": metadata.source_type,
        "domain": metadata.domain,
        "input_type": metadata.input_type,
    }

    for field_name, field_value in required_fields.items():

        is_present = (
            field_value is not None
            and str(field_value).strip() != ""
        )

        add_check(
            result,
            f"metadata_{field_name}",
            is_present,
            f"Value: {field_value}"
        )

        if not is_present:
            add_error(
                result,
                f"Missing required metadata: {field_name}"
            )

    input_type = str(metadata.input_type).upper()

    input_type_valid = input_type in SUPPORTED_INPUT_TYPES

    add_check(
        result,
        "supported_input_type",
        input_type_valid,
        f"Input type: {input_type}"
    )

    if not input_type_valid:
        add_error(
            result,
            f"Unsupported input type: {input_type}"
        )

    sampling_rate = metadata.sampling_rate_hz

    if sampling_rate is not None:

        rate_valid = (
            isinstance(sampling_rate, (int, float))
            and sampling_rate > 0
        )

        add_check(
            result,
            "sampling_rate",
            rate_valid,
            f"Sampling rate: {sampling_rate} Hz"
        )

        if not rate_valid:
            add_error(
                result,
                "Sampling rate must be a positive number."
            )

    dimensions = metadata.dimensions

    if dimensions is not None:

        dimensions_valid = (
            isinstance(dimensions, list)
            and all(
                isinstance(dimension, int)
                and dimension >= 0
                for dimension in dimensions
            )
        )

        add_check(
            result,
            "dimensions",
            dimensions_valid,
            f"Dimensions: {dimensions}"
        )

        if not dimensions_valid:
            add_error(
                result,
                "Dimensions must be a list of non-negative integers."
            )


def validate_immutability_policy(record, result):

    is_immutable = (
        record.raw_data_immutable is True
    )

    add_check(
        result,
        "raw_data_immutable",
        is_immutable,
        "Raw input modification is not permitted."
    )

    if not is_immutable:
        add_error(
            result,
            "Raw data immutability policy violation."
        )


def validate_file(
    record,
    result,
    max_file_size_mb=DEFAULT_MAX_FILE_SIZE_MB
):

    if record.file_path is None:

        add_check(
            result,
            "file_path",
            True,
            "No file path supplied; in-memory data may be used."
        )

        return

    file_path = Path(record.file_path)

    exists = file_path.exists()

    add_check(
        result,
        "file_exists",
        exists,
        str(file_path)
    )

    if not exists:

        add_error(
            result,
            f"File does not exist: {file_path}"
        )

        return

    is_file = file_path.is_file()

    add_check(
        result,
        "is_regular_file",
        is_file,
        str(file_path)
    )

    if not is_file:

        add_error(
            result,
            f"Path is not a regular file: {file_path}"
        )

        return

    file_size_bytes = file_path.stat().st_size
    file_size_mb = file_size_bytes / (1024 ** 2)

    size_valid = (
        file_size_mb <= max_file_size_mb
    )

    add_check(
        result,
        "file_size",
        size_valid,
        f"{file_size_mb:.4f} MB"
    )

    if not size_valid:

        add_error(
            result,
            (
                f"File exceeds maximum permitted size: "
                f"{max_file_size_mb} MB"
            )
        )


def validate_format_compatibility(record, result):

    if record.file_path is None:

        add_check(
            result,
            "format_compatibility",
            True,
            "No file path supplied."
        )

        return

    detected = detect_format(
        file_path=record.file_path
    )

    detected_type = str(
        detected.get("input_type", "UNKNOWN")
    ).upper()

    declared_type = str(
        record.metadata.input_type
    ).upper()

    if not detected.get("detected", False):

        add_warning(
            result,
            (
                "File format could not be identified: "
                f"{record.file_path}"
            )
        )

        add_check(
            result,
            "format_compatibility",
            True,
            "Unknown format; manual review may be required."
        )

        return

    compatible = (
        declared_type == detected_type
        or declared_type == "UNKNOWN"
    )

    add_check(
        result,
        "format_compatibility",
        compatible,
        (
            f"Declared: {declared_type}; "
            f"Detected: {detected_type}"
        )
    )

    if not compatible:

        add_error(
            result,
            (
                "Declared input type does not match detected "
                f"format: {declared_type} vs {detected_type}"
            )
        )


def validate_in_memory_data(record, result):

    if record.data is None:

        add_check(
            result,
            "in_memory_data",
            True,
            "No in-memory payload supplied."
        )

        return

    data_supported = isinstance(
        record.data,
        (
            dict,
            list,
            tuple,
            str,
            bytes,
            int,
            float
        )
    )

    add_check(
        result,
        "in_memory_data",
        data_supported,
        f"Data type: {type(record.data).__name__}"
    )

    if not data_supported:

        add_warning(
            result,
            (
                "Data type is not one of the basic supported "
                "validation types."
            )
        )


def validate_record(
    record,
    max_file_size_mb=DEFAULT_MAX_FILE_SIZE_MB
):

    result = create_validation_result()

    if not validate_record_type(record, result):

        result["status"] = "REJECTED"
        return result

    validate_metadata(record, result)
    validate_immutability_policy(record, result)

    validate_file(
        record,
        result,
        max_file_size_mb=max_file_size_mb
    )

    validate_format_compatibility(record, result)
    validate_in_memory_data(record, result)

    if result["valid"]:

        result["status"] = "VALIDATED"
        record.status = "VALIDATED"

    else:

        result["status"] = "REJECTED"
        record.status = "REJECTED"

    record.validation_messages = (
        result["errors"] + result["warnings"]
    )

    return result
