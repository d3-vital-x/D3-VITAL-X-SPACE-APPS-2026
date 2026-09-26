# ============================================================
# D³ VITAL-X SPACE INTELLIGENCE PLATFORM
# Module 13 — video_adapter.py
#
# Purpose:
# Public video / camera input adapter for the LIVE / WOW mode.
#
# Design principles:
# - Raw video is preserved
# - No scientific interpretation
# - No medical diagnosis
# - No biological damage claim
# - No automatic enhancement of raw frames
# - No smoothing / clipping / interpolation / averaging
# - Technical metadata + frame-level QC only
# - UnifiedDataRecord integration
#
# Public framework only:
# Proprietary intelligence / feature engine is NOT included.
# ============================================================

from pathlib import Path
from datetime import datetime, timezone
from dataclasses import asdict
from typing import Any, Dict, Optional, Union, Iterator
import hashlib
import json
import os
import re
import tempfile

# ------------------------------------------------------------
# 1. Project configuration
# ------------------------------------------------------------
PROJECT_ROOT = Path(
    "/content/D3-VITAL-X-Space-Intelligence-Platform"
)
MODULE_NAME = "video_adapter"
MODULE_VERSION = "1.0.0"
DEFAULT_MAX_FRAMES = 300
DEFAULT_FRAME_STEP = 1

# ------------------------------------------------------------
# 2. Load Unified Data Layer
# ------------------------------------------------------------
import importlib.util
import sys

SCHEMA_PATH = (
    PROJECT_ROOT / "04_UNIFIED_DATA_LAYER" / "data_schema.py"
)

def _load_schema_module():
    """
    Dynamically load the public Unified Data Layer schema.
    """
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Unified schema not found: {SCHEMA_PATH}"
        )

    module_name = "d3_vital_x_video_data_schema"
    if module_name in sys.modules:
        return sys.modules[module_name]

    spec = importlib.util.spec_from_file_location(
        module_name, SCHEMA_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(
            f"Could not create import specification for "
            f"{SCHEMA_PATH}"
        )

    module = importlib.util.module_from_spec(spec)
    # Required for dataclass/module resolution.
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

_schema = _load_schema_module()
DataMetadata = _schema.DataMetadata
UnifiedDataRecord = _schema.UnifiedDataRecord
InputType = _schema.InputType
DataDomain = _schema.DataDomain
DataStatus = _schema.DataStatus

# ------------------------------------------------------------
# 3. Optional OpenCV dependency
# ------------------------------------------------------------
def ensure_opencv():
    """
    Import OpenCV only when video functionality is requested.
    Returns: cv2 module
    """
    try:
        import cv2
        return cv2
    except ImportError as exc:
        raise ImportError(
            "OpenCV is required for video processing. "
            "Install it with: pip install opencv-python"
        ) from exc

# ------------------------------------------------------------
# 4. Basic utilities
# ------------------------------------------------------------
def utc_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(
        timezone.utc
    ).isoformat()

def calculate_sha256(
    source: Union[str, Path, bytes, bytearray]
) -> str:
    """
    Calculate SHA-256 for a file or bytes.
    """
    digest = hashlib.sha256()
    if isinstance(
        source, (bytes, bytearray)
    ):
        digest.update(
            bytes(source)
        )
        return digest.hexdigest()

    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    with path.open("rb") as f:
        for chunk in iter(
            lambda: f.read(1024 * 1024), b""
        ):
            digest.update(chunk)

    return digest.hexdigest()

def generate_dataset_id(
    source_name: str,
    raw_hash: str
) -> str:
    """
    Generate deterministic video dataset ID.
    """
    seed = (
        f"{source_name}|"
        f"{raw_hash}"
    )
    short_hash = hashlib.sha256(
        seed.encode("utf-8")
    ).hexdigest()[:16]
    return f"VIDEO-{short_hash}"

def safe_filename(
    name: str
) -> str:
    """
    Generate filesystem-safe filename.
    """
    name = str(name)
    name = re.sub(
        r"[^A-Za-z0-9._-]+", "_", name
    )
    name = name.strip("._")
    return name or "video_input"

# ------------------------------------------------------------
# 5. Supported video formats
# ------------------------------------------------------------
SUPPORTED_VIDEO_EXTENSIONS = {
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".webm",
    ".mpeg",
    ".mpg",
    ".m4v",
    ".wmv",
    ".3gp",
}

def is_supported_video_file(
    source: Union[str, Path]
) -> bool:
    """
    Check whether the file extension is supported.
    """
    path = Path(source)
    return (
        path.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS
    )

# ------------------------------------------------------------
# 6. Video metadata inspection
# ------------------------------------------------------------
def inspect_video(
    source: Union[str, Path]
) -> Dict[str, Any]:
    """
    Inspect technical video metadata using OpenCV.
    No frame transformation is performed.
    """
    cv2 = ensure_opencv()
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(
            f"Video not found: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"Video source is not a file: {path}"
        )

    capture = cv2.VideoCapture(
        str(path)
    )
    if not capture.isOpened():
        raise RuntimeError(
            f"OpenCV could not open video: {path}"
        )

    try:
        frame_count = int(
            capture.get(
                cv2.CAP_PROP_FRAME_COUNT
            )
        )
        fps = float(
            capture.get(
                cv2.CAP_PROP_FPS
            )
        )
        width = int(
            capture.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )
        height = int(
            capture.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )

        duration_seconds = None
        if fps > 0 and frame_count > 0:
            duration_seconds = (
                frame_count / fps
            )

        codec_value = int(
            capture.get(
                cv2.CAP_PROP_FOURCC
            )
        )
        codec = "".join(
            [
                chr(
                    (codec_value >> (8 * i)) & 0xFF
                )
                for i in range(4)
            ]
        )
    finally:
        capture.release()

    return {
        "filename": path.name,
        "path": str(path),
        "extension": path.suffix.lower(),
        "size_bytes": path.stat().st_size,
        "sha256": calculate_sha256(path),
        "frame_count": frame_count,
        "fps": fps,
        "width": width,
        "height": height,
        "duration_seconds": duration_seconds,
        "codec": codec,
        "opened_successfully": True,
        "inspected_at": utc_timestamp(),
    }

# ------------------------------------------------------------
# 7. Technical video validation
# ------------------------------------------------------------
def validate_video_structure(
    source: Union[str, Path]
) -> Dict[str, Any]:
    """
    Technical validation only.
    This function does NOT evaluate:
    - medical meaning
    - biological damage
    - disease
    - radiation effects
    - physical interpretation
    - mission safety
    """
    issues = []
    warnings = []

    path = Path(source)
    if not path.exists():
        issues.append(
            "Video file does not exist."
        )
        return {
            "valid": False,
            "issues": issues,
            "warnings": warnings,
            "checked_at": utc_timestamp(),
        }

    if not path.is_file():
        issues.append(
            "Source is not a regular file."
        )
        return {
            "valid": False,
            "issues": issues,
            "warnings": warnings,
            "checked_at": utc_timestamp(),
        }

    if path.stat().st_size == 0:
        issues.append(
            "Video file is empty."
        )
        return {
            "valid": False,
            "issues": issues,
            "warnings": warnings,
            "checked_at": utc_timestamp(),
        }

    if not is_supported_video_file(path):
        warnings.append(
            "File extension is not in the "
            "adapter's preferred video list."
        )

    try:
        metadata = inspect_video(path)
    except Exception as exc:
        issues.append(
            f"Video could not be opened: {exc}"
        )
        return {
            "valid": False,
            "issues": issues,
            "warnings": warnings,
            "checked_at": utc_timestamp(),
        }

    if metadata["frame_count"] <= 0:
        warnings.append(
            "Reported frame count is zero or unavailable."
        )

    if metadata["fps"] <= 0:
        warnings.append(
            "Reported FPS is zero or unavailable."
        )

    if metadata["width"] <= 0:
        issues.append(
            "Video width is invalid."
        )

    if metadata["height"] <= 0:
        issues.append(
            "Video height is invalid."
        )

    if metadata["duration_seconds"] is not None:
        if metadata["duration_seconds"] > 3600:
            warnings.append(
                "Video duration exceeds one hour."
            )

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "metadata": metadata,
        "checked_at": utc_timestamp(),
    }

# ------------------------------------------------------------
# 8. Frame iterator
# ------------------------------------------------------------
def iter_video_frames(
    source: Union[str, Path],
    max_frames: Optional[int] = DEFAULT_MAX_FRAMES,
    frame_step: int = DEFAULT_FRAME_STEP,
    include_timestamps: bool = True,
) -> Iterator[Dict[str, Any]]:
    """
    Yield raw decoded video frames sequentially.
    Important: Frames are returned exactly as decoded by OpenCV.
    No:
    - resizing
    - smoothing
    - clipping
    - interpolation
    - normalization
    - averaging
    - enhancement
    """
    cv2 = ensure_opencv()
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(path)

    if frame_step < 1:
        raise ValueError(
            "frame_step must be >= 1."
        )

    if max_frames is not None:
        if max_frames < 1:
            raise ValueError(
                "max_frames must be >= 1 or None."
            )

    capture = cv2.VideoCapture(
        str(path)
    )
    if not capture.isOpened():
        raise RuntimeError(
            f"Could not open video: {path}"
        )

    frame_index = 0
    yielded = 0

    try:
        while True:
            success, frame = capture.read()
            if not success:
                break

            if (
                frame_index % frame_step != 0
            ):
                frame_index += 1
                continue

            timestamp_ms = float(
                capture.get(
                    cv2.CAP_PROP_POS_MSEC
                )
            )

            item = {
                "frame_index": frame_index,
                "frame": frame,
            }

            if include_timestamps:
                item["timestamp_ms"] = (
                    timestamp_ms
                )
                item["timestamp_seconds"] = (
                    timestamp_ms / 1000.0
                )

            yield item

            yielded += 1
            frame_index += 1

            if (
                max_frames is not None
                and yielded >= max_frames
            ):
                break
    finally:
        capture.release()

# ------------------------------------------------------------
# 9. Frame technical summary
# ------------------------------------------------------------
def frame_summary(
    frame,
    frame_index: int = 0,
    timestamp_seconds: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Return technical information about a decoded frame.
    No image enhancement or scientific analysis.
    """
    shape = getattr(
        frame, "shape", None
    )
    dtype = getattr(
        frame, "dtype", None
    )

    summary = {
        "frame_index": frame_index,
        "shape": (
            list(shape) if shape is not None else None
        ),
        "dtype": (
            str(dtype) if dtype is not None else None
        ),
        "timestamp_seconds": (
            timestamp_seconds
        ),
    }

    if shape is not None:
        if len(shape) >= 2:
            summary["height"] = int(
                shape[0]
            )
            summary["width"] = int(
                shape[1]
            )
        if len(shape) == 3:
            summary["channels"] = int(
                shape[2]
            )
        elif len(shape) == 2:
            summary["channels"] = 1

    return summary

# ------------------------------------------------------------
# 10. Frame-level QC
# ------------------------------------------------------------
def validate_frame(
    frame
) -> Dict[str, Any]:
    """
    Basic technical frame QC.
    No scientific interpretation.
    """
    issues = []
    warnings = []

    if frame is None:
        issues.append(
            "Frame is None."
        )
        return {
            "valid": False,
            "issues": issues,
            "warnings": warnings,
        }

    shape = getattr(
        frame, "shape", None
    )
    if shape is None:
        issues.append(
            "Frame has no detectable shape."
        )
    else:
        if len(shape) < 2:
            issues.append(
                "Frame has fewer than two dimensions."
            )
        if any(
            int(value) <= 0 for value in shape
        ):
            issues.append(
                "Frame contains an invalid dimension."
            )

    dtype = getattr(
        frame, "dtype", None
    )
    if dtype is None:
        warnings.append(
            "Frame dtype unavailable."
        )

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
    }

# ------------------------------------------------------------
# 11. Video → UnifiedDataRecord
# ------------------------------------------------------------
def video_to_unified_record(
    source: Union[str, Path],
    source_uri: Optional[str] = None,
    dataset_id: Optional[str] = None,
    domain: Optional[DataDomain] = None,
    description: str = "",
    license_info: str = "",
    anonymized: bool = False,
    extra_metadata: Optional[Dict[str, Any]] = None,
    validate: bool = True,
) -> UnifiedDataRecord:
    """
    Convert a video source into UnifiedDataRecord.
    The original video remains file-backed.
    No frames are transformed or stored inside the UnifiedDataRecord by this adapter.
    """
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(path)

    if not path.is_file():
        raise ValueError(
            f"Source is not a file: {path}"
        )

    raw_hash = calculate_sha256(path)

    if dataset_id is None:
        dataset_id = generate_dataset_id(
            path.name, raw_hash
        )

    # Safe domain fallback resolution
    if domain is None:
        if hasattr(DataDomain, "GENERAL"):
            domain = DataDomain.GENERAL
        elif hasattr(DataDomain, "OTHER"):
            domain = DataDomain.OTHER
        else:
            domain = list(DataDomain)[0]

    # Safe InputType fallback resolution
    if hasattr(InputType, "VIDEO"):
        input_type_val = InputType.VIDEO
    elif hasattr(InputType, "MEDIA"):
        input_type_val = InputType.MEDIA
    elif hasattr(InputType, "STREAM"):
        input_type_val = InputType.STREAM
    else:
        input_type_val = list(InputType)[0]

    validation_messages = []
    status = DataStatus.RECEIVED
    video_metadata = None

    if validate:
        validation = validate_video_structure(
            path
        )
        validation_messages.extend(
            validation["issues"]
        )
        validation_messages.extend(
            [
                f"WARNING: {warning}"
                for warning in validation["warnings"]
            ]
        )
        video_metadata = validation.get(
            "metadata"
        )

        if validation["valid"]:
            status = DataStatus.VALIDATED
        else:
            status = DataStatus.REJECTED
    else:
        try:
            video_metadata = inspect_video(
                path
            )
        except Exception:
            video_metadata = None

    dimensions = None
    sampling_rate_hz = None
    acquisition_time = None

    if video_metadata:
        dimensions = [
            video_metadata.get(
                "height"
            ),
            video_metadata.get(
                "width"
            ),
            video_metadata.get(
                "frame_count"
            ),
        ]
        fps = video_metadata.get(
            "fps"
        )
        if fps and fps > 0:
            sampling_rate_hz = fps

    metadata = DataMetadata(
        dataset_id=dataset_id,
        source_name=path.name,
        source_type="VIDEO",
        source_uri=(
            source_uri or str(path)
        ),
        domain=domain,
        input_type=input_type_val,
        description=description,
        units="",
        dimensions=dimensions,
        sampling_rate_hz=sampling_rate_hz,
        acquisition_time=acquisition_time,
        created_at=utc_timestamp(),
        license_info=license_info,
        anonymized=anonymized,
        provenance={
            "adapter": MODULE_NAME,
            "adapter_version": MODULE_VERSION,
            "source_uri": source_uri,
            "raw_sha256": raw_hash,
            "raw_data_preserved": True,
            "video_metadata": video_metadata,
        },
        extra=(
            extra_metadata or {}
        ),
    )

    record = UnifiedDataRecord(
        metadata=metadata,
        data=None,
        file_path=str(path),
        raw_data_hash=raw_hash,
        raw_data_immutable=True,
        status=status,
        validation_messages=(
            validation_messages
        ),
        processing_history=[
            {
                "timestamp": utc_timestamp(),
                "module": MODULE_NAME,
                "operation": "video_to_unified_record",
                "raw_data_modified": False,
            }
        ],
    )

    return record

# ------------------------------------------------------------
# 12. Compact record summary
# ------------------------------------------------------------
def summarize_video_record(
    record: UnifiedDataRecord
) -> Dict[str, Any]:
    """
    Return a JSON-safe summary.
    """
    metadata = record.metadata
    return {
        "dataset_id": metadata.dataset_id,
        "source_name": metadata.source_name,
        "source_type": metadata.source_type,
        "source_uri": metadata.source_uri,
        "domain": (
            metadata.domain.value
            if hasattr(
                metadata.domain, "value"
            )
            else str(
                metadata.domain
            )
        ),
        "input_type": (
            metadata.input_type.value
            if hasattr(
                metadata.input_type, "value"
            )
            else str(
                metadata.input_type
            )
        ),
        "status": (
            record.status.value
            if hasattr(
                record.status, "value"
            )
            else str(
                record.status
            )
        ),
        "file_path": record.file_path,
        "raw_data_hash": record.raw_data_hash,
        "raw_data_immutable": record.raw_data_immutable,
        "dimensions": metadata.dimensions,
        "sampling_rate_hz": metadata.sampling_rate_hz,
        "validation_messages": record.validation_messages,
        "processing_history_count": len(
            record.processing_history
        ),
    }

# ------------------------------------------------------------
# 13. Video provenance JSON
# ------------------------------------------------------------
def video_provenance_json(
    record: UnifiedDataRecord,
    indent: int = 2
) -> str:
    """
    Serialize a compact provenance record.
    """
    return json.dumps(
        summarize_video_record(record),
        indent=indent,
        ensure_ascii=False,
        default=str,
    )

# ------------------------------------------------------------
# 14. Synthetic test video generator
# ------------------------------------------------------------
def create_synthetic_test_video(
    output_path: Union[str, Path],
    width: int = 160,
    height: int = 120,
    fps: float = 10.0,
    frame_count: int = 20,
) -> Path:
    """
    Create a synthetic test video.
    This is NOT scientific data.
    It is only used to test the adapter.
    The generated frames contain simple geometric patterns so that no external dataset is required.
    """
    cv2 = ensure_opencv()
    output_path = Path(
        output_path
    )
    output_path.parent.mkdir(
        parents=True, exist_ok=True
    )

    fourcc = cv2.VideoWriter_fourcc(
        *"mp4v"
    )
    writer = cv2.VideoWriter(
        str(output_path),
        fourcc,
        fps,
        (width, height)
    )

    if not writer.isOpened():
        raise RuntimeError(
            "Could not initialize "
            "OpenCV VideoWriter."
        )

    try:
        for i in range(frame_count):
            # Simple deterministic synthetic pattern.
            frame = (
                __import__("numpy")
                .zeros(
                    ( height, width, 3 ),
                    dtype="uint8"
                )
            )
            x = ( i * 5 ) % max( width, 1 )
            y = ( i * 3 ) % max( height, 1 )
            cv2.circle(
                frame, (x, y), 12, (255, 255, 255), -1
            )
            writer.write(frame)
    finally:
        writer.release()

    return output_path

# ------------------------------------------------------------
# 15. Full local self-test
# ------------------------------------------------------------
def run_video_adapter_test() -> Dict[str, Any]:
    """
    Run a completely local video adapter test.
    No external video source required.
    """
    test_dir = Path(
        tempfile.mkdtemp(
            prefix="d3_video_adapter_test_"
        )
    )
    test_video = (
        test_dir / "synthetic_live_test.mp4"
    )

    # Create synthetic video.
    create_synthetic_test_video(
        output_path=test_video,
        width=160,
        height=120,
        fps=10.0,
        frame_count=20,
    )

    # Inspect.
    inspection = inspect_video(
        test_video
    )

    # Validate.
    validation = validate_video_structure(
        test_video
    )

    # Convert to unified record.
    record = video_to_unified_record(
        test_video,
        source_uri=(
            "synthetic://VIDEO_TEST_FIXTURE"
        ),
        description=(
            "Synthetic video adapter "
            "test fixture."
        ),
        license_info="Test fixture",
        anonymized=True,
        extra_metadata={
            "test_fixture": True,
            "external_source": False,
        },
    )

    # Read a few frames.
    frame_results = []
    for item in iter_video_frames(
        test_video,
        max_frames=3,
    ):
        frame_qc = validate_frame(
            item["frame"]
        )
        frame_results.append({
            "frame_index": item["frame_index"],
            "timestamp_seconds": item[
                "timestamp_seconds"
            ],
            "qc": frame_qc,
            "summary": frame_summary(
                item["frame"],
                frame_index=item[
                    "frame_index"
                ],
                timestamp_seconds=item[
                    "timestamp_seconds"
                ],
            ),
        })

    # Integrity check.
    hash_before = calculate_sha256(
        test_video
    )
    hash_after = calculate_sha256(
        test_video
    )
    integrity_ok = (
        hash_before == hash_after == record.raw_data_hash
    )

    # Assertions.
    assert (
        inspection[
            "opened_successfully"
        ] is True
    )
    assert (
        inspection["frame_count"] > 0
    )
    assert (
        inspection["fps"] > 0
    )
    assert (
        inspection["width"] == 160
    )
    assert (
        inspection["height"] == 120
    )
    assert (
        validation["valid"] is True
    )
    assert (
        len(frame_results) == 3
    )
    assert (
        all(
            item["qc"]["valid"]
            for item in frame_results
        )
    )
    assert (
        record.raw_data_immutable is True
    )
    assert (
        integrity_ok is True
    )

    return {
        "passed": True,
        "module": MODULE_NAME,
        "version": MODULE_VERSION,
        "test_dir": str(test_dir),
        "test_video": str(test_video),
        "inspection": inspection,
        "validation": validation,
        "frame_results": frame_results,
        "record_summary": summarize_video_record(
            record
        ),
        "integrity_preserved": integrity_ok,
        "network_used": False,
        "message": (
            "Video adapter synthetic "
            "test passed. Raw video "
            "integrity preserved."
        ),
    }

# ------------------------------------------------------------
# 16. Module information
# ------------------------------------------------------------
def module_info() -> Dict[str, Any]:
    """
    Return module metadata.
    """
    return {
        "module": MODULE_NAME,
        "version": MODULE_VERSION,
        "purpose": (
            "Video and camera-input "
            "adapter for the D³ VITAL-X "
            "LIVE / WOW research mode."
        ),
        "supported_extensions": sorted(
            SUPPORTED_VIDEO_EXTENSIONS
        ),
        "raw_data_policy": (
            "Original video remains "
            "file-backed and hashed."
        ),
        "frame_transformation": False,
        "scientific_interpretation": False,
        "medical_diagnosis": False,
        "biological_damage_detection": False,
        "proprietary_core_included": False,
    }

print(
    f"🎥 {MODULE_NAME}.py loaded "
    f"(v{MODULE_VERSION})"
)
print( "🔒 Raw-video preservation: ENABLED" )
print( "🧪 Scientific interpretation: DISABLED" )
print( "🩻 Medical diagnosis: DISABLED" )
print( "🚀 Unified Data Layer integration: ENABLED" )
