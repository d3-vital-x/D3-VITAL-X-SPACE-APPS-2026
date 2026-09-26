# ============================================================
# OVERWRITE AND PUSH COMPLETE MODULE 12 (nasa_adapter.py)
# ============================================================
import subprocess
from pathlib import Path

PROJECT_ROOT = Path("/content/D3-VITAL-X-Space-Intelligence-Platform")
ADAPTER_PATH = PROJECT_ROOT / "03_INPUT_ADAPTERS" / "nasa_adapter.py"

nasa_adapter_code = '''# ============================================================
# D³ VITAL-X SPACE INTELLIGENCE PLATFORM
# Module 12 — nasa_adapter.py
#
# Purpose:
# NASA / space-data ingestion adapter for the public framework.
#
# Design principles:
# - Preserve downloaded/raw data
# - No scientific interpretation inside the adapter
# - No smoothing / clipping / interpolation / averaging
# - Technical validation only
# - UnifiedDataRecord integration
# - Optional NASA API-key support via environment variable
# - Provenance tracking
#
# Public framework only:
# This module does NOT contain the proprietary intelligence core.
# ============================================================

from pathlib import Path
from datetime import datetime, timezone
from dataclasses import asdict
from typing import Any, Dict, Optional, Union
import hashlib
import json
import os
import re
import tempfile
import urllib.request
import urllib.error
import urllib.parse
import mimetypes

# ------------------------------------------------------------
# 1. Load Unified Data Layer
# ------------------------------------------------------------
import importlib.util
import sys

PROJECT_ROOT = Path("/content/D3-VITAL-X-Space-Intelligence-Platform")
SCHEMA_PATH = (
    PROJECT_ROOT / "04_UNIFIED_DATA_LAYER" / "data_schema.py"
)

def _load_schema_module():
    """
    Dynamically load the public Unified Data Layer schema.
    This avoids assuming the project root is already on sys.path.
    """
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Unified schema not found: {SCHEMA_PATH}"
        )

    module_name = "d3_vital_x_data_schema"
    if module_name in sys.modules:
        return sys.modules[module_name]

    spec = importlib.util.spec_from_file_location(
        module_name, SCHEMA_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(
            f"Could not create import specification for {SCHEMA_PATH}"
        )

    module = importlib.util.module_from_spec(spec)
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
# 2. Constants
# ------------------------------------------------------------
MODULE_NAME = "nasa_adapter"
MODULE_VERSION = "1.0.0"
DEFAULT_TIMEOUT = 30
NASA_API_BASE = "https://api.nasa.gov"

SUPPORTED_EXTENSIONS = {
    ".csv": "csv",
    ".json": "json",
    ".txt": "text",
    ".xml": "xml",
    ".fits": "fits",
    ".fit": "fits",
    ".hdf5": "hdf5",
    ".h5": "hdf5",
    ".nc": "netcdf",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".tif": "image",
    ".tiff": "image",
}

# ------------------------------------------------------------
# 3. Utility functions
# ------------------------------------------------------------
def utc_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()

def calculate_sha256(
    source: Union[str, Path, bytes, bytearray]
) -> str:
    """
    Calculate SHA-256 hash.
    Supports:
    - file path
    - bytes
    - bytearray
    """
    digest = hashlib.sha256()
    if isinstance(source, (bytes, bytearray)):
        digest.update(bytes(source))
        return digest.hexdigest()

    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()

def generate_dataset_id(
    source_name: str,
    raw_hash: str
) -> str:
    """
    Generate a deterministic dataset identifier.
    """
    seed = f"{source_name}|{raw_hash}"
    short_hash = hashlib.sha256(
        seed.encode("utf-8")
    ).hexdigest()[:16]
    return f"NASA-{short_hash}"

def detect_format(
    filename: Optional[str] = None,
    content_type: Optional[str] = None
) -> str:
    """
    Detect a basic NASA dataset format.
    This is technical format detection only.
    """
    if filename:
        suffix = Path(filename).suffix.lower()
        if suffix in SUPPORTED_EXTENSIONS:
            return SUPPORTED_EXTENSIONS[suffix]

    if content_type:
        content_type = content_type.lower()
        if "json" in content_type:
            return "json"
        if "csv" in content_type:
            return "csv"
        if "xml" in content_type:
            return "xml"
        if "fits" in content_type:
            return "fits"
        if "text" in content_type:
            return "text"
        if content_type.startswith("image/"):
            return "image"

    return "unknown"

def safe_filename(name: str) -> str:
    """
    Create a filesystem-safe filename.
    Does not modify the source data itself.
    """
    name = str(name)
    name = re.sub(
        r"[^A-Za-z0-9._-]+", "_", name
    )
    name = name.strip("._")
    return name or "nasa_dataset"

# ------------------------------------------------------------
# 4. NASA API key handling
# ------------------------------------------------------------
def get_nasa_api_key(
    explicit_key: Optional[str] = None
) -> Optional[str]:
    """
    Obtain NASA API key.
    Priority:
    1. Explicit function argument
    2. NASA_API_KEY environment variable
    No key is hard-coded.
    """
    if explicit_key:
        return explicit_key
    return os.environ.get("NASA_API_KEY")

def build_nasa_api_url(
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None
) -> str:
    """
    Build a NASA API URL.
    Example: build_nasa_api_url(
        "/planetary/apod", {"date": "2026-09-20"}
    )
    """
    if not endpoint:
        raise ValueError("NASA API endpoint cannot be empty.")

    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        base_url = endpoint
    else:
        endpoint = endpoint.lstrip("/")
        base_url = f"{NASA_API_BASE}/{endpoint}"

    query = dict(params or {})
    key = get_nasa_api_key(api_key)

    if key and "api_key" not in query:
        query["api_key"] = key

    if query:
        encoded = urllib.parse.urlencode(
            query, doseq=True
        )
        separator = "&" if "?" in base_url else "?"
        return f"{base_url}{separator}{encoded}"

    return base_url

# ------------------------------------------------------------
# 5. NASA URL fetcher
# ------------------------------------------------------------
def fetch_nasa_resource(
    url: str,
    output_dir: Union[str, Path],
    filename: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
    api_key: Optional[str] = None,
    user_agent: str = "D3-VITAL-X-NASA-Adapter/1.0"
) -> Dict[str, Any]:
    """
    Download a NASA resource to disk.
    The downloaded bytes are preserved exactly as received.
    No:
    - smoothing
    - clipping
    - interpolation
    - normalization
    - averaging
    - scientific transformation
    """
    if not url:
        raise ValueError("URL cannot be empty.")

    output_dir = Path(output_dir)
    output_dir.mkdir(
        parents=True, exist_ok=True
    )

    final_url = build_nasa_api_url(
        url, api_key=api_key
    )
    parsed = urllib.parse.urlparse(final_url)

    original_name = Path(
        urllib.parse.unquote(parsed.path)
    ).name

    if not original_name:
        original_name = "nasa_resource"

    if filename:
        original_name = filename

    filename = safe_filename(original_name)
    output_path = output_dir / filename

    request = urllib.request.Request(
        final_url,
        headers={
            "User-Agent": user_agent,
            "Accept": "*/*",
        }
    )

    started_at = utc_timestamp()

    try:
        with urllib.request.urlopen(
            request, timeout=timeout
        ) as response:
            content_type = response.headers.get(
                "Content-Type", ""
            )

            with output_path.open("wb") as f:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)

            status_code = getattr(
                response, "status", 200
            )
            final_response_url = response.geturl()

    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"NASA resource request failed "
            f"(HTTP {exc.code}): {exc.reason}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"NASA resource connection failed: {exc.reason}"
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            f"NASA resource download failed: {exc}"
        ) from exc

    raw_hash = calculate_sha256(output_path)
    detected_format = detect_format(
        filename=filename,
        content_type=content_type
    )

    return {
        "source_url": url,
        "resolved_url": final_response_url,
        "local_path": str(output_path),
        "filename": filename,
        "content_type": content_type,
        "format": detected_format,
        "http_status": status_code,
        "size_bytes": output_path.stat().st_size,
        "sha256": raw_hash,
        "download_started_at": started_at,
        "download_completed_at": utc_timestamp(),
        "raw_data_immutable": True,
    }

# ------------------------------------------------------------
# 6. Local NASA resource inspection
# ------------------------------------------------------------
def inspect_nasa_file(
    source: Union[str, Path]
) -> Dict[str, Any]:
    """
    Inspect a downloaded/local NASA dataset.
    Technical inspection only.
    """
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(
            f"NASA file not found: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"NASA source is not a file: {path}"
        )

    size_bytes = path.stat().st_size
    suffix = path.suffix.lower()
    detected_format = detect_format(
        filename=path.name
    )
    mime_type, _ = mimetypes.guess_type(
        str(path)
    )

    return {
        "filename": path.name,
        "path": str(path),
        "size_bytes": size_bytes,
        "extension": suffix,
        "format": detected_format,
        "mime_type": mime_type,
        "sha256": calculate_sha256(path),
        "exists": True,
        "is_file": True,
        "inspected_at": utc_timestamp(),
    }

# ------------------------------------------------------------
# 7. NASA JSON inspection
# ------------------------------------------------------------
def inspect_nasa_json(
    source: Union[str, Path]
) -> Dict[str, Any]:
    """
    Parse a NASA JSON resource for structural inspection.
    The original file is NOT modified.
    """
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(path)

    with path.open(
        "r", encoding="utf-8"
    ) as f:
        payload = json.load(f)

    if isinstance(payload, dict):
        root_type = "object"
        key_count = len(payload)
        keys_preview = list(payload.keys())[:20]
    elif isinstance(payload, list):
        root_type = "array"
        key_count = None
        keys_preview = []
    else:
        root_type = type(payload).__name__
        key_count = None
        keys_preview = []

    return {
        "path": str(path),
        "format": "json",
        "root_type": root_type,
        "key_count": key_count,
        "keys_preview": keys_preview,
        "valid_json": True,
        "inspected_at": utc_timestamp(),
    }

# ------------------------------------------------------------
# 8. NASA resource validation
# ------------------------------------------------------------
def validate_nasa_structure(
    source: Union[str, Path]
) -> Dict[str, Any]:
    """
    Technical structural validation.
    This does NOT validate:
    - scientific correctness
    - physical interpretation
    - mission suitability
    - biological meaning
    - medical meaning
    """
    issues = []
    warnings = []

    path = Path(source)
    if not path.exists():
        issues.append("Source file does not exist.")
        return {
            "valid": False,
            "issues": issues,
            "warnings": warnings,
            "checked_at": utc_timestamp(),
        }

    if not path.is_file():
        issues.append("Source is not a regular file.")
        return {
            "valid": False,
            "issues": issues,
            "warnings": warnings,
            "checked_at": utc_timestamp(),
        }

    size_bytes = path.stat().st_size
    if size_bytes == 0:
        issues.append("File is empty.")

    detected_format = detect_format(
        filename=path.name
    )

    if detected_format == "unknown":
        warnings.append(
            "File format could not be confidently detected."
        )

    if size_bytes > 5 * 1024 * 1024 * 1024:
        warnings.append(
            "Large dataset detected; streaming or chunked "
            "processing may be required."
        )

    valid = len(issues) == 0

    return {
        "valid": valid,
        "issues": issues,
        "warnings": warnings,
        "filename": path.name,
        "size_bytes": size_bytes,
        "format": detected_format,
        "checked_at": utc_timestamp(),
    }

# ------------------------------------------------------------
# 9. NASA → UnifiedDataRecord
# ------------------------------------------------------------
def nasa_to_unified_record(
    source: Union[str, Path],
    source_url: Optional[str] = None,
    dataset_id: Optional[str] = None,
    domain: Optional[DataDomain] = None,
    description: str = "",
    license_info: str = "",
    anonymized: bool = False,
    extra_metadata: Optional[Dict[str, Any]] = None,
    validate: bool = True,
) -> UnifiedDataRecord:
    """
    Convert a NASA/space dataset into UnifiedDataRecord.
    IMPORTANT: This function does not interpret the scientific content.
    Data remains file-backed to avoid unnecessary transformation.
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

    detected_format = detect_format(
        filename=path.name
    )

    if domain is None:
        domain = DataDomain.ASTROPHYSICS

    validation_messages = []
    status = DataStatus.RECEIVED

    if validate:
        validation = validate_nasa_structure(path)
        validation_messages.extend(
            validation["issues"]
        )
        validation_messages.extend(
            [
                f"WARNING: {warning}"
                for warning in validation["warnings"]
            ]
        )
        if validation["valid"]:
            status = DataStatus.VALIDATED
        else:
            status = DataStatus.FAILED

    metadata = DataMetadata(
        dataset_id=dataset_id,
        source_name=path.name,
        source_type="NASA",
        source_uri=source_url or str(path),
        domain=domain,
        input_type=InputType.SPECTRAL if detected_format == "fits" else InputType.GENERIC,
        description=description,
        units="",
        dimensions=None,
        sampling_rate_hz=None,
        acquisition_time=None,
        created_at=utc_timestamp(),
        license_info=license_info,
        anonymized=anonymized,
        provenance={
            "adapter": MODULE_NAME,
            "adapter_version": MODULE_VERSION,
            "source_url": source_url,
            "retrieval_timestamp": utc_timestamp(),
            "raw_sha256": raw_hash,
            "raw_data_preserved": True,
        },
        extra=extra_metadata or {},
    )

    record = UnifiedDataRecord(
        metadata=metadata,
        data=None,
        file_path=str(path),
        raw_data_hash=raw_hash,
        raw_data_immutable=True,
        status=status,
        validation_messages=validation_messages,
        processing_history=[
            {
                "timestamp": utc_timestamp(),
                "module": MODULE_NAME,
                "operation": "nasa_to_unified_record",
                "raw_data_modified": False,
            }
        ],
    )

    return record

# ------------------------------------------------------------
# 10. JSON-safe record summary
# ------------------------------------------------------------
def summarize_nasa_record(
    record: UnifiedDataRecord
) -> Dict[str, Any]:
    """
    Produce a compact JSON-safe summary.
    """
    metadata = record.metadata
    return {
        "dataset_id": metadata.dataset_id,
        "source_name": metadata.source_name,
        "source_type": metadata.source_type,
        "source_uri": metadata.source_uri,
        "domain": (
            metadata.domain.value
            if hasattr(metadata.domain, "value")
            else str(metadata.domain)
        ),
        "input_type": (
            metadata.input_type.value
            if hasattr(metadata.input_type, "value")
            else str(metadata.input_type)
        ),
        "status": (
            record.status.value
            if hasattr(record.status, "value")
            else str(record.status)
        ),
        "file_path": record.file_path,
        "raw_data_hash": record.raw_data_hash,
        "raw_data_immutable": record.raw_data_immutable,
        "validation_messages": record.validation_messages,
        "processing_history_count": len(
            record.processing_history
        ),
    }

# ------------------------------------------------------------
# 11. NASA API JSON → temporary raw file
# ------------------------------------------------------------
def fetch_nasa_json(
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    output_dir: Optional[Union[str, Path]] = None,
    filename: Optional[str] = None,
    api_key: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """
    Fetch a NASA API JSON response and preserve it as a raw file.
    This is useful for structured NASA APIs.
    The JSON response is stored exactly as received.
    """
    if output_dir is None:
        output_dir = Path.cwd() / "nasa_raw"

    output_dir = Path(output_dir)
    output_dir.mkdir(
        parents=True, exist_ok=True
    )

    final_url = build_nasa_api_url(
        endpoint, params=params, api_key=api_key
    )

    parsed = urllib.parse.urlparse(
        final_url
    )

    if filename is None:
        endpoint_name = (
            Path(parsed.path).name or "nasa_api_response"
        )
        filename = safe_filename(
            f"{endpoint_name}.json"
        )

    result = fetch_nasa_resource(
        final_url,
        output_dir=output_dir,
        filename=filename,
        timeout=timeout,
        api_key=None,  # URL already contains query parameters.
    )

    return result

# ------------------------------------------------------------
# 12. Provenance JSON
# ------------------------------------------------------------
def nasa_provenance_json(
    record: UnifiedDataRecord,
    indent: int = 2
) -> str:
    """
    Serialize NASA record provenance safely.
    """
    payload = summarize_nasa_record(record)
    return json.dumps(
        payload, indent=indent, ensure_ascii=False, default=str
    )

# ------------------------------------------------------------
# 13. Self-test
# ------------------------------------------------------------
def run_nasa_adapter_test() -> Dict[str, Any]:
    """
    Run a local synthetic NASA-adapter test.
    No external NASA network request is required.
    """
    test_dir = Path(
        tempfile.mkdtemp(
            prefix="d3_nasa_adapter_test_"
        )
    )
    test_file = test_dir / "synthetic_nasa_test.json"

    synthetic_payload = {
        "source": "NASA_TEST_FIXTURE",
        "dataset_type": "synthetic",
        "timestamp": utc_timestamp(),
        "values": [
            1.0,
            2.0,
            3.0,
            4.0,
        ],
        "note": (
            "Synthetic test fixture only; "
            "not NASA observational data."
        ),
    }

    # Write a controlled test fixture.
    with test_file.open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(
            synthetic_payload, f, indent=2
        )

    # Inspect.
    inspection = inspect_nasa_file(
        test_file
    )
    json_inspection = inspect_nasa_json(
        test_file
    )
    validation = validate_nasa_structure(
        test_file
    )

    # Convert to unified record.
    record = nasa_to_unified_record(
        test_file,
        source_url=(
            "synthetic://NASA_TEST_FIXTURE"
        ),
        description=(
            "Synthetic NASA adapter test fixture."
        ),
        license_info="Test fixture",
        anonymized=True,
        extra_metadata={
            "test_fixture": True,
            "external_network_used": False,
        },
    )

    summary = summarize_nasa_record(
        record
    )

    # Integrity check.
    hash_before = calculate_sha256(
        test_file
    )
    hash_after = calculate_sha256(
        test_file
    )
    integrity_ok = (
        hash_before == hash_after == record.raw_data_hash
    )

    assert inspection["exists"] is True
    assert inspection["format"] == "json"
    assert json_inspection["valid_json"] is True
    assert validation["valid"] is True
    assert record.raw_data_immutable is True
    assert integrity_ok is True

    return {
        "passed": True,
        "module": MODULE_NAME,
        "version": MODULE_VERSION,
        "test_dir": str(test_dir),
        "file": str(test_file),
        "inspection": inspection,
        "json_inspection": json_inspection,
        "validation": validation,
        "record_summary": summary,
        "integrity_preserved": integrity_ok,
        "network_used": False,
        "message": (
            "NASA adapter synthetic test passed. "
            "Raw-data integrity preserved."
        ),
    }

# ------------------------------------------------------------
# 14. Module information
# ------------------------------------------------------------
def module_info() -> Dict[str, Any]:
    """
    Return public module metadata.
    """
    return {
        "module": MODULE_NAME,
        "version": MODULE_VERSION,
        "purpose": (
            "NASA and space-data ingestion into "
            "the D³ VITAL-X Unified Data Layer."
        ),
        "supported_formats": sorted(
            set(SUPPORTED_EXTENSIONS.values())
        ),
        "raw_data_policy": (
            "Input bytes are preserved; "
            "no scientific transformation is performed."
        ),
        "scientific_interpretation": False,
        "clinical_diagnosis": False,
        "proprietary_core_included": False,
    }

print(
    f"🛰️ {MODULE_NAME}.py loaded "
    f"(v{MODULE_VERSION})"
)
print( "🔒 Raw-data preservation: ENABLED" )
print( "🧪 Scientific interpretation inside adapter: DISABLED" )
print( "🚀 Unified Data Layer integration: ENABLED" )
'''

# ১. ফাইলটি সম্পূর্ণ কোড দিয়ে ওভাররাইট করা
ADAPTER_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(ADAPTER_PATH, "w", encoding="utf-8") as f:
    f.write(nasa_adapter_code)

print(f"📁 Fully written Module 12 to: {ADAPTER_PATH}")

# ২. গিটহাব রিপ্রোজিটরিতে Commit এবং Push
def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print(f"⚠️ {result.stderr.strip()}")
    else:
        print(f"✅ {result.stdout.strip()}")

run_cmd("git add -A")
run_cmd("git commit -m 'Update Module 12: nasa_adapter.py full source code implementation'")
run_cmd("git push origin main")

print("\n🚀 Complete Module 12 pushed to GitHub successfully!")
 Module 12 - nasa_adapter.py code here
