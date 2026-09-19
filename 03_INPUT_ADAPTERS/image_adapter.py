"""
D³ VITAL-X Image Input Adapter
Technical image metadata extraction and UnifiedDataRecord-compatible conversion.
The original image remains immutable.
No pixel transformation is performed.
"""

import hashlib
import importlib.util
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any, Dict, Optional

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    Image = None
    PILLOW_AVAILABLE = False


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_image_dependency():
    if not PILLOW_AVAILABLE:
        raise ImportError("Pillow is required. Run: pip install Pillow")


def calculate_sha256(file_path: Path) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def generate_dataset_id(file_path: Path, raw_hash: str) -> str:
    source = f"{file_path.name}|{raw_hash}"
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
    return f"image_{digest}"


def inspect_image(file_path: str) -> Dict[str, Any]:
    ensure_image_dependency()
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")
    if not path.is_file():
        raise ValueError(f"Path is not a regular file: {path}")

    raw_hash = calculate_sha256(path)

    with Image.open(path) as image:
        bands = image.getbands()
        metadata = {
            "file_name": path.name,
            "file_path": str(path),
            "file_extension": path.suffix.lower(),
            "format": image.format,
            "mode": image.mode,
            "bands": list(bands),
            "channel_count": len(bands),
            "width": image.size[0],
            "height": image.size[1],
            "dimensions": [image.size[1], image.size[0]],
            "pixel_count": image.size[0] * image.size[1],
            "file_size_bytes": path.stat().st_size,
            "raw_sha256": raw_hash,
            "has_exif": bool(image.getexif()),
            "is_animated": bool(getattr(image, "is_animated", False)),
            "frame_count": int(getattr(image, "n_frames", 1)),
            "inspected_at": utc_timestamp(),
        }

    return metadata


def load_image_array(file_path: str, preserve_mode: bool = True):
    ensure_image_dependency()
    import numpy as np

    path = Path(file_path)
    with Image.open(path) as image:
        if preserve_mode:
            return np.array(image)
        return np.array(image.convert("RGB"))


def validate_image_structure(image_metadata: Dict[str, Any]) -> Dict[str, Any]:
    errors = []
    warnings = []

    if image_metadata.get("width", 0) <= 0:
        errors.append("Image width is missing or invalid.")
    if image_metadata.get("height", 0) <= 0:
        errors.append("Image height is missing or invalid.")
    if image_metadata.get("channel_count", 0) <= 0:
        errors.append("Channel count is missing or invalid.")

    if image_metadata.get("is_animated"):
        warnings.append("Animated or multi-frame image detected.")
    if image_metadata.get("has_exif"):
        warnings.append("EXIF metadata detected.")

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def image_to_unified_record(
    file_path: str,
    source_name: Optional[str] = None,
    description: str = "",
    domain: Optional[Any] = None,
    license_info: str = "Not specified",
    anonymized: Optional[bool] = None,
    load_pixels: bool = False,
    extra_metadata: Optional[Dict[str, Any]] = None,
):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")

    # Dynamic Schema Loading
    schema_path = path.parents[1] / "04_UNIFIED_DATA_LAYER" / "data_schema.py"
    if schema_path.exists():
        spec = importlib.util.spec_from_file_location("d3_schema", str(schema_path))
        schema_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(schema_module)
        
        UnifiedDataRecord = schema_module.UnifiedDataRecord
        DataMetadata = schema_module.DataMetadata
        InputType = schema_module.InputType
        DataDomain = schema_module.DataDomain
        DataStatus = schema_module.DataStatus
    else:
        raise FileNotFoundError(f"Schema not found at {schema_path}")

    if source_name is None:
        source_name = path.name

    image_metadata = inspect_image(file_path=str(path))
    structure_report = validate_image_structure(image_metadata)
    raw_hash = image_metadata["raw_sha256"]
    dataset_id = generate_dataset_id(path, raw_hash)

    if domain is None:
        domain = DataDomain.UNKNOWN

    metadata_extra = {
        "adapter": "image_adapter",
        "adapter_version": "1.0.0",
        "image_format": image_metadata["format"],
        "image_mode": image_metadata["mode"],
        "bands": image_metadata["bands"],
        "channel_count": image_metadata["channel_count"],
        "width": image_metadata["width"],
        "height": image_metadata["height"],
        "pixel_count": image_metadata["pixel_count"],
        "file_size_bytes": image_metadata["file_size_bytes"],
        "has_exif": image_metadata["has_exif"],
        "is_animated": image_metadata["is_animated"],
        "frame_count": image_metadata["frame_count"],
        "structure_report": structure_report,
        "raw_sha256": raw_hash,
        "scientific_processing_performed": False,
        "pixel_transformations_performed": False,
        "created_at": utc_timestamp(),
    }

    if extra_metadata is not None:
        metadata_extra.update(extra_metadata)

    data_payload = {
        "file_path": str(path),
        "format": image_metadata["format"],
        "mode": image_metadata["mode"],
        "width": image_metadata["width"],
        "height": image_metadata["height"],
        "bands": image_metadata["bands"],
        "channel_count": image_metadata["channel_count"],
        "pixel_count": image_metadata["pixel_count"],
        "structure_report": structure_report,
        "pixels_loaded": False,
    }

    if load_pixels:
        pixel_array = load_image_array(file_path=str(path), preserve_mode=True)
        data_payload["pixels"] = pixel_array
        data_payload["pixels_loaded"] = True

    metadata = DataMetadata(
        dataset_id=dataset_id,
        source_name=source_name,
        source_type="IMAGE",
        source_uri=str(path),
        domain=domain,
        input_type=InputType.UNKNOWN,
        description=description,
        units={},
        dimensions={
            "height": image_metadata["height"],
            "width": image_metadata["width"],
            "channels": image_metadata["channel_count"],
        },
        sampling_rate_hz=None,
        acquisition_time=None,
        created_at=utc_timestamp(),
        license_info=license_info,
        anonymized=anonymized,
        provenance={
            "source_file": str(path),
            "raw_sha256": raw_hash,
            "adapter": "image_adapter",
            "raw_data_preserved": True,
            "pixel_transformations_performed": False,
            "scientific_processing_performed": False,
        },
        extra=metadata_extra,
    )

    return UnifiedDataRecord(
        metadata=metadata,
        data=data_payload,
        file_path=str(path),
        raw_data_hash=raw_hash,
        raw_data_immutable=True,
        status=DataStatus.RECEIVED,
        validation_messages=(
            structure_report["errors"] + structure_report["warnings"]
        ),
        processing_history=[],
    )


def summarize_image_record(record) -> Dict[str, Any]:
    data = record.data or {}
    structure_report = data.get("structure_report", {})

    return {
        "dataset_id": record.metadata.dataset_id,
        "source_name": record.metadata.source_name,
        "input_type": str(record.metadata.input_type),
        "format": data.get("format"),
        "mode": data.get("mode"),
        "width": data.get("width"),
        "height": data.get("height"),
        "channel_count": data.get("channel_count"),
        "structure_valid": structure_report.get("valid"),
        "raw_sha256": record.raw_data_hash,
        "raw_data_immutable": record.raw_data_immutable,
        "status": str(record.status),
        "generated_at": utc_timestamp(),
    }
