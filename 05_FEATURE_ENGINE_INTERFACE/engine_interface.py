# ============================================================
# D³ VITAL-X SPACE INTELLIGENCE PLATFORM
# Module 14 — engine_interface.py
#
# BLACK-BOX ENGINE INTERFACE
#
# Purpose:
#   Define a strict public contract between:
#
#       Unified Data Layer
#              │
#              ▼
#       BLACK-BOX ENGINE INTERFACE
#              │
#              ▼
#       Private Intelligence Core
#
# IMPORTANT:
#   This module does NOT implement the proprietary engine.
#
# Public:
#   - Request schema
#   - Response schema
#   - validation
#   - provenance
#   - execution status
#   - capability declaration
#   - safe error handling
#
# Private:
#   - intelligence algorithms
#   - model parameters
#   - feature-generation logic
#   - proprietary equations
#   - internal optimization
#   - MCMC / parameter inference
#   - engine implementation
#
# Safety principles:
#   - No eval()
#   - No exec()
#   - No arbitrary code execution
#   - No private source loading
#   - No scientific interpretation inside interface
#   - No medical diagnosis
#   - No flight certification
#   - No modification of raw input
# ============================================================

from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
    asdict,
)
from datetime import (
    datetime,
    timezone,
)
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
    Mapping,
)
import hashlib
import json
import uuid


# ------------------------------------------------------------
# 1. Module metadata
# ------------------------------------------------------------

MODULE_NAME = "engine_interface"
MODULE_VERSION = "1.0.0"

INTERFACE_VERSION = "1.0"

PRIVATE_CORE_INCLUDED = False

RAW_DATA_MODIFICATION_ALLOWED = False

MEDICAL_DIAGNOSIS_SUPPORTED = False

FLIGHT_CERTIFICATION_SUPPORTED = False


# ------------------------------------------------------------
# 2. Utility functions
# ------------------------------------------------------------

def utc_timestamp() -> str:
    """
    Return an ISO-8601 UTC timestamp.
    """
    return datetime.now(
        timezone.utc
    ).isoformat()


def calculate_sha256_bytes(
    payload: bytes,
) -> str:
    """
    Calculate SHA-256 for bytes.
    """
    return hashlib.sha256(
        payload
    ).hexdigest()


def canonical_json(
    payload: Mapping[str, Any],
) -> str:
    """
    Convert a mapping into deterministic JSON.

    Used for request/provenance fingerprints.

    This does not execute or interpret code.
    """
    return json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(
            ",",
            ":",
        ),
        default=str,
    )


def calculate_object_hash(
    payload: Mapping[str, Any],
) -> str:
    """
    Calculate a deterministic SHA-256 hash
    from a JSON-compatible mapping.
    """
    encoded = canonical_json(
        payload
    ).encode("utf-8")

    return calculate_sha256_bytes(
        encoded
    )


def generate_request_id() -> str:
    """
    Generate a unique engine request ID.
    """
    return (
        "ENG-"
        + uuid.uuid4().hex[:16].upper()
    )


# ------------------------------------------------------------
# 3. Interface status
# ------------------------------------------------------------

class EngineStatus(str, Enum):
    """
    High-level engine execution states.
    """

    READY = "READY"
    ACCEPTED = "ACCEPTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_CONFIGURED = "NOT_CONFIGURED"


# ------------------------------------------------------------
# 4. Analysis mode
# ------------------------------------------------------------

class AnalysisMode(str, Enum):
    """
    Public analysis intent.

    These are interface-level labels only.

    They do not expose the internal algorithm.
    """

    GENERAL = "GENERAL"
    SPACE = "SPACE"
    BIOMEDICAL_RESEARCH = "BIOMEDICAL_RESEARCH"
    TIME_SERIES = "TIME_SERIES"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    NASA = "NASA"
    VALIDATION = "VALIDATION"


# ------------------------------------------------------------
# 5. Input reference
# ------------------------------------------------------------

@dataclass
class EngineInputReference:
    """
    Reference to an input dataset.

    The interface receives a reference rather than
    embedding arbitrary raw data into the request.

    This helps maintain the public/private boundary.
    """

    dataset_id: str
    source_type: str
    file_path: Optional[str] = None
    source_uri: Optional[str] = None
    raw_data_hash: Optional[str] = None
    raw_data_immutable: bool = True
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def validate(self) -> List[str]:
        """
        Validate the input reference.
        """
        errors: List[str] = []

        if not self.dataset_id:
            errors.append(
                "dataset_id is required."
            )

        if not self.source_type:
            errors.append(
                "source_type is required."
            )

        if not self.raw_data_immutable:
            errors.append(
                "raw_data_immutable must be True."
            )

        if (
            self.file_path is None
            and self.source_uri is None
        ):
            errors.append(
                "Either file_path or source_uri "
                "must be provided."
            )

        if self.raw_data_hash is not None:
            if len(self.raw_data_hash) != 64:
                errors.append(
                    "raw_data_hash must be "
                    "a SHA-256 hexadecimal hash."
                )
            elif any(
                char not in "0123456789abcdefABCDEF"
                for char in self.raw_data_hash
            ):
                errors.append(
                    "raw_data_hash contains "
                    "invalid hexadecimal characters."
                )

        return errors


# ------------------------------------------------------------
# 6. Engine request
# ------------------------------------------------------------

@dataclass
class EngineRequest:
    """
    Public request contract sent toward
    the black-box intelligence core.

    IMPORTANT:
        This object contains NO proprietary
        algorithmic implementation.
    """

    request_id: str
    interface_version: str
    mode: AnalysisMode
    input_reference: EngineInputReference
    requested_outputs: List[str] = field(
        default_factory=list
    )
    options: Dict[str, Any] = field(
        default_factory=dict
    )
    provenance: Dict[str, Any] = field(
        default_factory=dict
    )
    created_at: str = field(
        default_factory=utc_timestamp
    )

    def validate(self) -> List[str]:
        """
        Validate request structure.
        """
        errors: List[str] = []

        if not self.request_id:
            errors.append(
                "request_id is required."
            )

        if not self.interface_version:
            errors.append(
                "interface_version is required."
            )

        if not isinstance(
            self.mode,
            AnalysisMode,
        ):
            errors.append(
                "mode must be an AnalysisMode."
            )

        errors.extend(
            self.input_reference.validate()
        )

        if not isinstance(
            self.requested_outputs,
            list,
        ):
            errors.append(
                "requested_outputs must be a list."
            )

        if not isinstance(
            self.options,
            dict,
        ):
            errors.append(
                "options must be a dictionary."
            )

        if not isinstance(
            self.provenance,
            dict,
        ):
            errors.append(
                "provenance must be a dictionary."
            )

        return errors

    def fingerprint(self) -> str:
        """
        Create a deterministic request fingerprint.

        This identifies the interface-level request
        without exposing private engine internals.
        """
        payload = {
            "interface_version": self.interface_version,
            "mode": self.mode.value,
            "input_reference": asdict(self.input_reference),
            "requested_outputs": list(self.requested_outputs),
            "options": self.options,
        }

        return calculate_object_hash(
            payload
        )


# ------------------------------------------------------------
# 7. Safe output value
# ------------------------------------------------------------

@dataclass
class EngineOutput:
    """
    One output returned by the black-box engine.

    The interface does not assume that an output
    is a diagnosis or a physical conclusion.
    """

    name: str
    value: Any
    unit: Optional[str] = None
    confidence: Optional[float] = None
    uncertainty: Optional[Any] = None
    interpretation_class: str = "COMPUTATIONAL_OUTPUT"
    human_review_required: bool = True
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def validate(self) -> List[str]:
        """
        Validate output metadata.
        """
        errors: List[str] = []

        if not self.name:
            errors.append(
                "Output name is required."
            )

        if self.confidence is not None:
            try:
                confidence = float(self.confidence)
                if not (0.0 <= confidence <= 1.0):
                    errors.append(
                        "confidence must be between 0 and 1."
                    )
            except (TypeError, ValueError):
                errors.append(
                    "confidence must be numeric."
                )

        if not isinstance(
            self.human_review_required,
            bool,
        ):
            errors.append(
                "human_review_required must be boolean."
            )

        return errors


# ------------------------------------------------------------
# 8. Engine response
# ------------------------------------------------------------

@dataclass
class EngineResponse:
    """
    Public response contract returned from
    the black-box engine boundary.
    """

    request_id: str
    interface_version: str
    status: EngineStatus
    outputs: List[EngineOutput] = field(
        default_factory=list
    )
    messages: List[str] = field(
        default_factory=list
    )
    warnings: List[str] = field(
        default_factory=list
    )
    errors: List[str] = field(
        default_factory=list
    )
    execution_metadata: Dict[str, Any] = field(
        default_factory=dict
    )
    provenance: Dict[str, Any] = field(
        default_factory=dict
    )
    completed_at: Optional[str] = None

    def validate(self) -> List[str]:
        """
        Validate response structure.
        """
        errors: List[str] = []

        if not self.request_id:
            errors.append(
                "request_id is required."
            )

        if not self.interface_version:
            errors.append(
                "interface_version is required."
            )

        if not isinstance(
            self.status,
            EngineStatus,
        ):
            errors.append(
                "status must be an EngineStatus."
            )

        if not isinstance(
            self.outputs,
            list,
        ):
            errors.append(
                "outputs must be a list."
            )
        else:
            for index, output in enumerate(self.outputs):
                if not isinstance(output, EngineOutput):
                    errors.append(
                        f"outputs[{index}] is not EngineOutput."
                    )
                    continue

                errors.extend(
                    [
                        f"outputs[{index}]: {message}"
                        for message in output.validate()
                    ]
                )

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert response to JSON-safe dictionary.
        """
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """
        Serialize response to JSON.
        """
        return json.dumps(
            self.to_dict(),
            indent=indent,
            ensure_ascii=False,
            default=str,
        )


# ------------------------------------------------------------
# 9. Interface capability declaration
# ------------------------------------------------------------

@dataclass(frozen=True)
class EngineCapabilities:
    """
    Public capability declaration.

    This deliberately describes WHAT the interface
    can request, not HOW the private engine works.
    """

    interface_version: str = INTERFACE_VERSION
    black_box: bool = True
    proprietary_core_exposed: bool = False
    raw_data_modification: bool = False
    medical_diagnosis: bool = False
    flight_certification: bool = False
    supported_modes: Tuple[str, ...] = (
        AnalysisMode.GENERAL.value,
        AnalysisMode.SPACE.value,
        AnalysisMode.BIOMEDICAL_RESEARCH.value,
        AnalysisMode.TIME_SERIES.value,
        AnalysisMode.IMAGE.value,
        AnalysisMode.VIDEO.value,
        AnalysisMode.NASA.value,
        AnalysisMode.VALIDATION.value,
    )
    supported_output_types: Tuple[str, ...] = (
        "METRIC",
        "FEATURE",
        "ANOMALY_SCORE",
        "TRANSITION_INDICATOR",
        "QUALITY_INDICATOR",
        "UNCERTAINTY",
        "VISUALIZATION_REFERENCE",
        "EXPLANATION_REFERENCE",
    )


# ------------------------------------------------------------
# 10. Engine provider protocol
# ------------------------------------------------------------

class EngineProvider:
    """
    Abstract provider contract.

    This class intentionally contains NO proprietary
    intelligence implementation.

    A private implementation can implement the same
    contract outside the public repository.
    """

    provider_name = "UNCONFIGURED"
    provider_version = "0.0"

    def capabilities(self) -> EngineCapabilities:
        """
        Return public capability declaration.
        """
        return EngineCapabilities()

    def health_check(self) -> Dict[str, Any]:
        """
        Public health/status check.

        Default state is NOT_CONFIGURED.
        """
        return {
            "status": EngineStatus.NOT_CONFIGURED.value,
            "provider": self.provider_name,
            "provider_version": self.provider_version,
            "available": False,
            "black_box": True,
            "checked_at": utc_timestamp(),
        }

    def execute(
        self,
        request: EngineRequest,
    ) -> EngineResponse:
        """
        Execute an engine request.

        The public implementation deliberately does
        not contain the private intelligence core.
        """
        raise NotImplementedError(
            "No intelligence engine is configured "
            "in the public interface."
        )


# ------------------------------------------------------------
# 11. Null / safe engine provider
# ------------------------------------------------------------

class NullEngineProvider(EngineProvider):
    """
    Safe default provider.

    It validates requests but never executes
    proprietary intelligence.

    This allows the public repository and dashboard
    to operate without exposing the private core.
    """

    provider_name = "PUBLIC_NULL_PROVIDER"
    provider_version = "1.0.0"

    def health_check(self) -> Dict[str, Any]:
        return {
            "status": EngineStatus.NOT_CONFIGURED.value,
            "provider": self.provider_name,
            "provider_version": self.provider_version,
            "available": False,
            "black_box": True,
            "proprietary_core_exposed": False,
            "checked_at": utc_timestamp(),
        }

    def execute(
        self,
        request: EngineRequest,
    ) -> EngineResponse:
        """
        Validate request and return a safe
        NOT_CONFIGURED response.
        """
        validation_errors = request.validate()

        if validation_errors:
            return EngineResponse(
                request_id=request.request_id,
                interface_version=request.interface_version,
                status=EngineStatus.REJECTED,
                errors=validation_errors,
                warnings=[
                    "Request was rejected at the public interface validation layer."
                ],
                provenance={
                    "interface": MODULE_NAME,
                    "interface_version": MODULE_VERSION,
                    "request_fingerprint": request.fingerprint(),
                    "private_core_executed": False,
                },
                completed_at=utc_timestamp(),
            )

        return EngineResponse(
            request_id=request.request_id,
            interface_version=request.interface_version,
            status=EngineStatus.NOT_CONFIGURED,
            outputs=[],
            messages=[
                "Request accepted by the public interface contract.",
                "No proprietary intelligence engine is configured in the public repository.",
            ],
            warnings=[
                "This response is an interface test result, not a scientific analysis.",
                "No medical or mission-critical decision should be derived from this response.",
            ],
            errors=[],
            execution_metadata={
                "provider": self.provider_name,
                "provider_version": self.provider_version,
                "execution_performed": False,
                "private_core_executed": False,
                "raw_data_modified": False,
            },
            provenance={
                "interface": MODULE_NAME,
                "interface_version": MODULE_VERSION,
                "request_fingerprint": request.fingerprint(),
                "private_core_exposed": False,
            },
            completed_at=utc_timestamp(),
        )


# ------------------------------------------------------------
# 12. Engine interface facade
# ------------------------------------------------------------

class EngineInterface:
    """
    Main public facade for engine communication.

    The application talks to this object rather than
    directly importing a proprietary engine.
    """

    def __init__(
        self,
        provider: Optional[EngineProvider] = None,
    ):
        self.provider = (
            provider
            if provider is not None
            else NullEngineProvider()
        )

    def capabilities(self) -> EngineCapabilities:
        """
        Return public capabilities.
        """
        return self.provider.capabilities()

    def health_check(self) -> Dict[str, Any]:
        """
        Return engine health/status.
        """
        return self.provider.health_check()

    def create_request(
        self,
        input_reference: EngineInputReference,
        mode: AnalysisMode = AnalysisMode.GENERAL,
        requested_outputs: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None,
        provenance: Optional[Dict[str, Any]] = None,
    ) -> EngineRequest:
        """
        Construct a validated interface request.
        """
        return EngineRequest(
            request_id=generate_request_id(),
            interface_version=INTERFACE_VERSION,
            mode=mode,
            input_reference=input_reference,
            requested_outputs=requested_outputs or [],
            options=options or {},
            provenance=provenance or {},
        )

    def execute(
        self,
        request: EngineRequest,
    ) -> EngineResponse:
        """
        Send request through the configured provider.
        """
        return self.provider.execute(request)


# ------------------------------------------------------------
# 13. Safe request builder from UnifiedDataRecord
# ------------------------------------------------------------

def request_from_unified_record(
    record: Any,
    mode: AnalysisMode = AnalysisMode.GENERAL,
    requested_outputs: Optional[List[str]] = None,
    options: Optional[Dict[str, Any]] = None,
) -> EngineRequest:
    """
    Build an EngineRequest from a UnifiedDataRecord.

    This function intentionally extracts only
    interface-relevant metadata.

    It does NOT copy the raw data into the request.
    """
    if not hasattr(record, "metadata"):
        raise TypeError("record must contain metadata.")

    metadata = record.metadata

    dataset_id = getattr(metadata, "dataset_id", None)
    source_type = getattr(metadata, "source_type", "UNKNOWN")
    source_uri = getattr(metadata, "source_uri", None)
    file_path = getattr(record, "file_path", None)
    raw_hash = getattr(record, "raw_data_hash", None)
    raw_immutable = getattr(record, "raw_data_immutable", True)

    input_reference = EngineInputReference(
        dataset_id=dataset_id or "",
        source_type=str(source_type),
        file_path=file_path,
        source_uri=source_uri,
        raw_data_hash=raw_hash,
        raw_data_immutable=bool(raw_immutable),
        metadata={
            "domain": str(getattr(metadata, "domain", "")),
            "input_type": str(getattr(metadata, "input_type", "")),
            "description": str(getattr(metadata, "description", "")),
        },
    )

    return EngineRequest(
        request_id=generate_request_id(),
        interface_version=INTERFACE_VERSION,
        mode=mode,
        input_reference=input_reference,
        requested_outputs=requested_outputs or [],
        options=options or {},
        provenance={
            "adapter": MODULE_NAME,
            "created_at": utc_timestamp(),
            "raw_data_modified": False,
        },
    )


# ------------------------------------------------------------
# 14. Response safety validation
# ------------------------------------------------------------

def validate_engine_response(
    response: EngineResponse,
) -> Dict[str, Any]:
    """
    Validate a response at the public boundary.
    """
    errors = response.validate()
    safety_warnings = []

    if response.status == EngineStatus.COMPLETED:
        safety_warnings.append(
            "Completed outputs are computational "
            "results and require domain-appropriate "
            "human review."
        )

    if not response.provenance:
        safety_warnings.append(
            "Response provenance is empty."
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": safety_warnings,
        "checked_at": utc_timestamp(),
    }


# ------------------------------------------------------------
# 15. Interface serialization helpers
# ------------------------------------------------------------

def request_to_dict(
    request: EngineRequest,
) -> Dict[str, Any]:
    """
    Serialize EngineRequest.
    """
    return asdict(request)


def request_to_json(
    request: EngineRequest,
    indent: int = 2,
) -> str:
    """
    Serialize EngineRequest as JSON.
    """
    return json.dumps(
        request_to_dict(request),
        indent=indent,
        ensure_ascii=False,
        default=str,
    )


def response_to_dict(
    response: EngineResponse,
) -> Dict[str, Any]:
    """
    Serialize EngineResponse.
    """
    return response.to_dict()


def response_to_json(
    response: EngineResponse,
    indent: int = 2,
) -> str:
    """
    Serialize EngineResponse as JSON.
    """
    return response.to_json(indent=indent)


# ------------------------------------------------------------
# 16. Public interface contract
# ------------------------------------------------------------

def interface_contract() -> Dict[str, Any]:
    """
    Return a public machine-readable contract.

    This intentionally contains no proprietary
    algorithmic details.
    """
    return {
        "interface_name": MODULE_NAME,
        "interface_version": INTERFACE_VERSION,
        "module_version": MODULE_VERSION,
        "architecture_role": "PUBLIC_TO_PRIVATE_BOUNDARY",
        "black_box": True,
        "private_core_exposed": False,
        "raw_data_modification": False,
        "medical_diagnosis": False,
        "flight_certification": False,
        "request_schema": [
            "request_id",
            "interface_version",
            "mode",
            "input_reference",
            "requested_outputs",
            "options",
            "provenance",
            "created_at",
        ],
        "response_schema": [
            "request_id",
            "interface_version",
            "status",
            "outputs",
            "messages",
            "warnings",
            "errors",
            "execution_metadata",
            "provenance",
            "completed_at",
        ],
        "supported_modes": [mode.value for mode in AnalysisMode],
        "supported_statuses": [status.value for status in EngineStatus],
    }


# ------------------------------------------------------------
# 17. Local self-test
# ------------------------------------------------------------

def run_engine_interface_test() -> Dict[str, Any]:
    """
    Run a completely local interface test.

    No proprietary engine is executed.
    No external network access is required.
    """
    # Synthetic input reference
    input_reference = EngineInputReference(
        dataset_id="TEST-DATASET-001",
        source_type="TIME_SERIES",
        file_path="/tmp/synthetic_signal.csv",
        source_uri="synthetic://test/signal",
        raw_data_hash="a" * 64,
        raw_data_immutable=True,
        metadata={
            "test_fixture": True,
            "description": "Synthetic interface test input",
        },
    )

    # Validate input reference
    input_errors = input_reference.validate()
    assert input_errors == []

    # Create interface
    interface = EngineInterface()
    capabilities = interface.capabilities()
    health = interface.health_check()

    # Create request
    request = interface.create_request(
        input_reference=input_reference,
        mode=AnalysisMode.TIME_SERIES,
        requested_outputs=[
            "METRIC",
            "QUALITY_INDICATOR",
            "ANOMALY_SCORE",
        ],
        options={"test_mode": True},
        provenance={"test_fixture": True},
    )

    # Request validation
    request_errors = request.validate()
    assert request_errors == []

    fingerprint = request.fingerprint()
    assert len(fingerprint) == 64

    # Execute through NULL provider
    response = interface.execute(request)
    assert response.status == EngineStatus.NOT_CONFIGURED
    assert response.request_id == request.request_id

    # Validate response
    response_validation = validate_engine_response(response)
    assert response_validation["valid"] is True

    # Contract
    contract = interface_contract()
    assert contract["black_box"] is True
    assert contract["private_core_exposed"] is False
    assert contract["raw_data_modification"] is False

    # Serialization
    request_json = request_to_json(request)
    response_json = response_to_json(response)
    assert isinstance(request_json, str)
    assert isinstance(response_json, str)

    # Return test result
    return {
        "passed": True,
        "module": MODULE_NAME,
        "module_version": MODULE_VERSION,
        "interface_version": INTERFACE_VERSION,
        "private_core_executed": False,
        "private_core_exposed": capabilities.proprietary_core_exposed,
        "raw_data_modification": capabilities.raw_data_modification,
        "health": health,
        "request_id": request.request_id,
        "request_fingerprint": fingerprint,
        "request_validation_errors": request_errors,
        "response_status": response.status.value,
        "response_validation": response_validation,
        "contract": contract,
        "message": (
            "Black-box engine interface test passed. "
            "No proprietary engine was executed."
        ),
    }


# ------------------------------------------------------------
# 18. Module information
# ------------------------------------------------------------

def module_info() -> Dict[str, Any]:
    """
    Return module metadata.
    """
    return {
        "module": MODULE_NAME,
        "version": MODULE_VERSION,
        "interface_version": INTERFACE_VERSION,
        "role": "BLACK_BOX_ENGINE_INTERFACE",
        "private_core_included": PRIVATE_CORE_INCLUDED,
        "raw_data_modification_allowed": RAW_DATA_MODIFICATION_ALLOWED,
        "medical_diagnosis_supported": MEDICAL_DIAGNOSIS_SUPPORTED,
        "flight_certification_supported": FLIGHT_CERTIFICATION_SUPPORTED,
        "security_principles": [
            "No eval",
            "No exec",
            "No arbitrary code execution",
            "No private source loading",
            "No proprietary algorithm exposure",
        ],
    }


# ------------------------------------------------------------
# 19. Load message
# ------------------------------------------------------------

print(f"🟥 {MODULE_NAME}.py loaded (v{MODULE_VERSION})")
print(f"🔒 Interface version: {INTERFACE_VERSION}")
print("🧠 Proprietary engine implementation: NOT INCLUDED")
print("🛡️ Raw-data modification: DISABLED")
print("🩻 Medical diagnosis: DISABLED")
print("🚀 Black-box contract: READY")
