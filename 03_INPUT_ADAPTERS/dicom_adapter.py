# ============================================================
# D³ VITAL-X SPACE INTELLIGENCE PLATFORM
# Module 11 — dicom_adapter.py
#
# Biomedical Research Input Adapter
#
# IMPORTANT:
# - Raw DICOM bytes are preserved.
# - No pixel transformation is performed.
# - No clinical diagnosis logic is included.
# - Sensitive patient-identifying DICOM tags are NOT exposed.
# - This module performs ingestion and technical inspection only.
# ============================================================

from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
import importlib.util

# ============================================================
# PROJECT PATH
# ============================================================
PROJECT_ROOT = Path("/content/D3-VITAL-X-Space-Intelligence-Platform")
SCHEMA_PATH = PROJECT_ROOT / "04_UNIFIED_DATA_LAYER" / "data_schema.py"

# ============================================================
# DYNAMIC SCHEMA LOADER
# ============================================================
def load_schema_module():
    """
    Dynamically load the project's public data_schema.py.
    This avoids requiring the project to be installed as a package.
    """
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Unified schema not found: {SCHEMA_PATH}")

    module_name = "d3_vital_x_data_schema"
    spec = importlib.util.spec_from_file_location(module_name, SCHEMA_PATH)
    if spec is None or spec.loader is None:
        raise ImportError("Could not create import specification for data_schema.py")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

_SCHEMA = load_schema_module()
UnifiedDataRecord = _SCHEMA.UnifiedDataRecord
DataMetadata = _SCHEMA.DataMetadata
InputType = _SCHEMA.InputType
DataDomain = _SCHEMA.DataDomain
DataStatus = _SCHEMA.DataStatus

# ============================================================
# OPTIONAL DEPENDENCY
# ============================================================
def ensure_pydicom():
    """
    Import pydicom.
    Raises a clear error if the dependency is unavailable.
    """
    try:
        import pydicom
        return pydicom
    except ImportError as exc:
        raise ImportError(
            "pydicom is required for DICOM processing. "
            "Install with: pip install pydicom"
        ) from exc

# ============================================================
# TIME / HASH UTILITIES
# ============================================================
def utc_timestamp():
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()

def calculate_sha256(data: bytes) -> str:
    """Calculate SHA-256 hash of raw DICOM bytes."""
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("calculate_sha256 expects bytes or bytearray.")
    return hashlib.sha256(bytes(data)).hexdigest()

# ============================================================
# DATASET ID
# ============================================================
def generate_dataset_id(raw_hash: str, prefix: str = "DICOM") -> str:
    """
    Generate a deterministic dataset identifier.
    The identifier is derived from the raw-data hash and does not expose
    patient-identifying metadata.
    """
    if not raw_hash:
        raise ValueError("raw_hash cannot be empty.")
    return f"{prefix}-{raw_hash[:16]}"

# ============================================================
# SAFE DICOM METADATA
# ============================================================
SAFE_DICOM_FIELDS = {
    "Modality": "Modality",
    "SOPClassUID": "SOPClassUID",
    "SOPInstanceUID": "SOPInstanceUID",
    "StudyInstanceUID": "StudyInstanceUID",
    "SeriesInstanceUID": "SeriesInstanceUID",
    "Rows": "Rows",
    "Columns": "Columns",
    "SamplesPerPixel": "SamplesPerPixel",
    "PhotometricInterpretation": "PhotometricInterpretation",
    "BitsAllocated": "BitsAllocated",
    "BitsStored": "BitsStored",
    "HighBit": "HighBit",
    "PixelRepresentation": "PixelRepresentation",
    "NumberOfFrames": "NumberOfFrames",
    "ImageType": "ImageType",
    "AcquisitionDateTime": "AcquisitionDateTime",
}

EXCLUDED_DICOM_FIELDS = {
    "PatientName",
    "PatientID",
    "PatientBirthDate",
    "PatientBirthTime",
    "PatientSex",
    "OtherPatientIDs",
    "OtherPatientNames",
    "PatientAddress",
    "PatientTelephoneNumbers",
    "PatientMotherBirthName",
    "InstitutionName",
    "InstitutionAddress",
    "ReferringPhysicianName",
    "PerformingPhysicianName",
    "OperatorsName",
    "StudyDescription",
    "SeriesDescription",
    "AccessionNumber",
}

def _safe_value(value):
    """Convert a pydicom value to JSON-friendly primitive form."""
    if value is None:
        return None
    if isinstance(value, bytes):
        return f"<bytes:{len(value)}>"
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [_safe_value(item) for item in value]
    try:
        return str(value)
    except Exception:
        return "<unserializable>"

def extract_safe_metadata(dataset):
    """
    Extract only a controlled subset of technical DICOM metadata.
    Sensitive patient-identifying fields are intentionally excluded.
    """
    metadata = {}
    for output_name, dicom_name in SAFE_DICOM_FIELDS.items():
        if dicom_name in EXCLUDED_DICOM_FIELDS:
            continue
        try:
            if hasattr(dataset, dicom_name):
                value = getattr(dataset, dicom_name)
                metadata[output_name] = _safe_value(value)
        except Exception:
            continue
    return metadata

# ============================================================
# DICOM INSPECTION
# ============================================================
def inspect_dicom(source, stop_before_pixels=True, force=False):
    """Inspect a DICOM file or raw bytes."""
    pydicom = ensure_pydicom()
    source_path = None
    if isinstance(source, (str, Path)):
        source_path = Path(source)
        if not source_path.exists():
            raise FileNotFoundError(f"DICOM file not found: {source_path}")
        dataset = pydicom.dcmread(
            str(source_path), stop_before_pixels=stop_before_pixels, force=force
        )
        raw_bytes = source_path.read_bytes()
    elif isinstance(source, (bytes, bytearray)):
        from io import BytesIO
        raw_bytes = bytes(source)
        dataset = pydicom.dcmread(
            BytesIO(raw_bytes), stop_before_pixels=stop_before_pixels, force=force
        )
    else:
        raise TypeError("source must be a file path or raw bytes.")

    raw_hash = calculate_sha256(raw_bytes)
    safe_metadata = extract_safe_metadata(dataset)

    return {
        "valid_dicom": True,
        "dataset_id": generate_dataset_id(raw_hash),
        "raw_sha256": raw_hash,
        "file_size_bytes": len(raw_bytes),
        "safe_metadata": safe_metadata,
        "pixel_data_loaded": not stop_before_pixels,
        "force_read": force,
        "inspected_at_utc": utc_timestamp(),
    }

# ============================================================
# DICOM STRUCTURE VALIDATION
# ============================================================
def validate_dicom_structure(source, force=False):
    """Perform technical DICOM structure validation."""
    pydicom = ensure_pydicom()
    try:
        if isinstance(source, (str, Path)):
            path = Path(source)
            if not path.exists():
                return {"valid": False, "message": "File does not exist."}
            dataset = pydicom.dcmread(
                str(path), stop_before_pixels=True, force=force
            )
            raw_bytes = path.read_bytes()
        elif isinstance(source, (bytes, bytearray)):
            from io import BytesIO
            raw_bytes = bytes(source)
            dataset = pydicom.dcmread(
                BytesIO(raw_bytes), stop_before_pixels=True, force=force
            )
        else:
            return {"valid": False, "message": "Source must be a path or bytes."}

        has_sop_class = hasattr(dataset, "SOPClassUID")
        has_sop_instance = hasattr(dataset, "SOPInstanceUID")
        has_modality = hasattr(dataset, "Modality")

        return {
            "valid": True,
            "readable": True,
            "has_sop_class_uid": has_sop_class,
            "has_sop_instance_uid": has_sop_instance,
            "has_modality": has_modality,
            "file_size_bytes": len(raw_bytes),
            "sha256": calculate_sha256(raw_bytes),
            "message": "DICOM structure readable. Technical checks passed.",
        }
    except Exception as exc:
        return {"valid": False, "readable": False, "message": str(exc)}

# ============================================================
# PIXEL DATA LOADING
# ============================================================
def load_dicom_pixels(source):
    """
    Load DICOM pixel data without modifying it.
    No smoothing, clipping, interpolation, normalization, or arbitrary averaging is performed.
    """
    pydicom = ensure_pydicom()
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"DICOM file not found: {path}")
        dataset = pydicom.dcmread(str(path), stop_before_pixels=False)
    elif isinstance(source, (bytes, bytearray)):
        from io import BytesIO
        dataset = pydicom.dcmread(BytesIO(bytes(source)), stop_before_pixels=False)
    else:
        raise TypeError("source must be a path or raw bytes.")

    if "PixelData" not in dataset:
        raise ValueError("DICOM dataset does not contain PixelData.")

    return dataset.pixel_array

# ============================================================
# DICOM → UNIFIED DATA RECORD
# ============================================================
def dicom_to_unified_record(
    source,
    source_name=None,
    source_uri=None,
    load_pixels=False,
    anonymized=False,
    description="DICOM biomedical research input for technical data exploration.",
    license_info=None,
):
    """Convert a DICOM input into UnifiedDataRecord."""
    pydicom = ensure_pydicom()

    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"DICOM file not found: {path}")
        raw_bytes = path.read_bytes()
        dataset = pydicom.dcmread(str(path), stop_before_pixels=not load_pixels)
        if source_name is None:
            source_name = path.name
    elif isinstance(source, (bytes, bytearray)):
        from io import BytesIO
        raw_bytes = bytes(source)
        dataset = pydicom.dcmread(
            BytesIO(raw_bytes), stop_before_pixels=not load_pixels
        )
        if source_name is None:
            source_name = "dicom_input"
    else:
        raise TypeError("source must be a DICOM path or raw bytes.")

    raw_hash = calculate_sha256(raw_bytes)
    dataset_id = generate_dataset_id(raw_hash)
    safe_metadata = extract_safe_metadata(dataset)

    modality = safe_metadata.get("Modality", "DICOM")
    rows = safe_metadata.get("Rows")
    columns = safe_metadata.get("Columns")
    dimensions = None
    if rows is not None and columns is not None:
        dimensions = [int(rows), int(columns)]

    data = None
    if load_pixels:
        if "PixelData" not in dataset:
            raise ValueError("DICOM file has no PixelData.")
        data = dataset.pixel_array

    metadata = DataMetadata(
        dataset_id=dataset_id,
        source_name=source_name,
        source_type="DICOM",
        source_uri=source_uri,
        domain=DataDomain.BIOMEDICAL,
        input_type=InputType.DICOM,
        description=description,
        units=None,
        dimensions=dimensions,
        sampling_rate_hz=None,
        acquisition_time=None,
        created_at=utc_timestamp(),
        license_info=license_info,
        anonymized=anonymized,
        provenance={
            "adapter": "dicom_adapter",
            "adapter_version": "0.1.0",
            "raw_sha256": raw_hash,
            "received_at_utc": utc_timestamp(),
            "safe_metadata": safe_metadata,
        },
        extra={
            "modality": modality,
            "pixels_loaded": load_pixels,
            "raw_data_preserved": True,
            "clinical_interpretation": False,
        },
    )

    return UnifiedDataRecord(
        metadata=metadata,
        data=data,
        file_path=str(source) if isinstance(source, (str, Path)) else None,
        raw_data_hash=raw_hash,
        raw_data_immutable=True,
        status=DataStatus.RECEIVED,
        validation_messages=[],
        processing_history=[],
    )

# ============================================================
# RECORD SUMMARY
# ============================================================
def summarize_dicom_record(record):
    """Generate a safe summary of a UnifiedDataRecord."""
    if not isinstance(record, UnifiedDataRecord):
        raise TypeError("record must be a UnifiedDataRecord.")
    metadata = record.metadata
    return {
        "dataset_id": metadata.dataset_id,
        "source_name": metadata.source_name,
        "source_type": metadata.source_type,
        "input_type": (
            metadata.input_type.value
            if hasattr(metadata.input_type, "value")
            else str(metadata.input_type)
        ),
        "domain": (
            metadata.domain.value
            if hasattr(metadata.domain, "value")
            else str(metadata.domain)
        ),
        "dimensions": metadata.dimensions,
        "raw_data_hash": record.raw_data_hash,
        "raw_data_immutable": record.raw_data_immutable,
        "status": (
            record.status.value
            if hasattr(record.status, "value")
            else str(record.status)
        ),
        "validation_messages": record.validation_messages,
    }

# ============================================================
# SAFE METADATA JSON
# ============================================================
def safe_metadata_json(source):
    """Return controlled technical metadata as JSON."""
    inspection = inspect_dicom(source, stop_before_pixels=True)
    return json.dumps(inspection, indent=2, default=str)

# ============================================================
# FUNCTIONAL TEST
# ============================================================
def run_dicom_adapter_test():
    """Basic functional test using synthetic in-memory DICOM."""
    pydicom = ensure_pydicom()
    from pydicom.dataset import FileDataset
    from pydicom.uid import (
        ExplicitVRLittleEndian,
        SecondaryCaptureImageStorage,
        generate_uid,
    )
    import numpy as np
    from io import BytesIO

    pixels = np.array([[0, 100, 200], [300, 400, 500]], dtype=np.uint16)

    file_meta = pydicom.dataset.FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    buffer = BytesIO()
    dataset = FileDataset(
        None, {}, file_meta=file_meta, preamble=b"\x00" * 128
    )
    dataset.is_little_endian = True
    dataset.is_implicit_VR = False
    dataset.SOPClassUID = SecondaryCaptureImageStorage
    dataset.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    dataset.Modality = "OT"
    dataset.Rows = 2
    dataset.Columns = 3
    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = "MONOCHROME2"
    dataset.BitsAllocated = 16
    dataset.BitsStored = 16
    dataset.HighBit = 15
    dataset.PixelRepresentation = 0
    dataset.PixelData = pixels.tobytes()
    dataset.save_as(buffer, write_like_original=False)
    raw_bytes = buffer.getvalue()

    inspection = inspect_dicom(raw_bytes)
    assert inspection["valid_dicom"] is True
    assert inspection["file_size_bytes"] > 0
    assert inspection["raw_sha256"]

    validation = validate_dicom_structure(raw_bytes)
    assert validation["valid"] is True
    assert validation["readable"] is True

    loaded_pixels = load_dicom_pixels(raw_bytes)
    assert loaded_pixels.shape == (2, 3)
    assert np.array_equal(loaded_pixels, pixels)

    record = dicom_to_unified_record(
        raw_bytes,
        source_name="synthetic_test.dcm",
        load_pixels=True,
        anonymized=True,
    )
    assert isinstance(record, UnifiedDataRecord)
    assert record.metadata.input_type == InputType.DICOM
    assert record.metadata.domain == DataDomain.BIOMEDICAL
    assert record.raw_data_immutable is True
    assert record.raw_data_hash == inspection["raw_sha256"]
    assert np.array_equal(record.data, pixels)

    safe_metadata = record.metadata.provenance["safe_metadata"]
    for forbidden in [
        "PatientName",
        "PatientID",
        "PatientBirthDate",
        "PatientAddress",
        "PatientTelephoneNumbers",
    ]:
        assert forbidden not in safe_metadata

    return {
        "status": "PASS",
        "message": "DICOM adapter functional test passed.",
        "dataset_id": record.metadata.dataset_id,
        "sha256": record.raw_data_hash,
        "dimensions": record.metadata.dimensions,
        "pixel_shape": list(record.data.shape),
    }

if __name__ == "__main__":
    result = run_dicom_adapter_test()
    print(json.dumps(result, indent=2, default=str))
