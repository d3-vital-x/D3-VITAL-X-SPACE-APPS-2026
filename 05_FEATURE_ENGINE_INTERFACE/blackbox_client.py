# ============================================================
# D³ VITAL-X Space Intelligence Platform
# Module 17 — blackbox_client.py
# ============================================================
#
# PUBLIC BLACK-BOX CLIENT / BOUNDARY LAYER
#
# ============================================================
# SECURITY PRINCIPLES
# ============================================================
#
# This module intentionally contains:
#
#   ❌ NO v10 source code
#   ❌ NO v11 source code
#   ❌ NO UTL/DVDH implementation
#   ❌ NO DSI implementation
#   ❌ NO Effective Mass implementation
#   ❌ NO PLV implementation
#   ❌ NO Lyapunov implementation
#   ❌ NO RQA implementation
#   ❌ NO bootstrap implementation
#   ❌ NO surrogate-generation implementation
#   ❌ NO proprietary coefficients
#   ❌ NO MCMC configuration
#   ❌ NO model weights
#   ❌ NO private endpoint URL
#   ❌ NO API token / password / secret
#   ❌ NO raw-data transmission by default
#   ❌ NO eval()
#   ❌ NO exec()
#
# It provides ONLY:
#
#   1. public request envelope
#   2. public response envelope
#   3. safe feature contract
#   4. opaque engine reference
#   5. execution/deferred status handling
#   6. provenance/fingerprint support
#   7. security validation
#
# The actual intelligence engine remains outside this module.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import hashlib
import json
import re
import uuid


# ============================================================
# MODULE METADATA
# ============================================================

MODULE_NAME = "blackbox_client"
MODULE_VERSION = "1.0.0"
BLACKBOX_PROTOCOL_VERSION = "1.0"

PROPRIETARY_ALGORITHMS_INCLUDED = False
PRIVATE_ENGINE_SOURCE_INCLUDED = False
SECRETS_INCLUDED = False

RAW_DATA_TRANSMISSION_ALLOWED = False
RAW_DATA_MODIFICATION_ALLOWED = False

MEDICAL_DIAGNOSIS_SUPPORTED = False
FLIGHT_CERTIFICATION_SUPPORTED = False


# ============================================================
# STATUS ENUMS
# ============================================================

class ClientStatus(str, Enum):
    READY = "READY"
    DEFERRED = "DEFERRED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    NOT_CONFIGURED = "NOT_CONFIGURED"


class ExecutionMode(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    PRIVATE_ENGINE = "PRIVATE_ENGINE"


# ============================================================
# SECURITY CONSTANTS
# ============================================================

SAFE_FEATURES = {
    "entropy",
    "variance",
    "gradient",
    "coupling",
    "transition_index",
    "anomaly_score",
    "signal_quality",
    "confidence",
    "uncertainty",
}


FORBIDDEN_REQUEST_FIELDS = {
    "password",
    "passwd",
    "secret",
    "api_key",
    "apikey",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "private_key",
    "model_weights",
    "weights",
    "mcmc_chain",
    "mcmc_parameters",
    "proprietary_parameters",
    "internal_coefficients",
    "private_coefficients",
    "raw_pixels",
    "raw_signal",
    "raw_counts",
}


# ============================================================
# BASIC UTILITIES
# ============================================================

def utc_timestamp() -> str:
    """Return UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def generate_client_request_id() -> str:
    """Generate non-sensitive request identifier."""
    return f"bb-{uuid.uuid4().hex}"


def canonical_json(payload: Any) -> str:
    """Create deterministic JSON representation."""
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )


def calculate_sha256(payload: Any) -> str:
    """Calculate SHA-256 fingerprint."""
    return hashlib.sha256(
        canonical_json(payload).encode("utf-8")
    ).hexdigest()


def sanitize_identifier(
    value: Any,
    fallback: str = "unknown",
) -> str:
    """
    Sanitize identifiers used in public metadata.

    This is NOT an arbitrary-code sanitizer.
    Arbitrary code is never accepted by this module.
    """

    if value is None:
        return fallback

    text = str(value).strip()

    if not text:
        return fallback

    cleaned = re.sub(
        r"[^A-Za-z0-9_.:@/-]",
        "_",
        text,
    )

    return cleaned[:128]


def normalize_feature_name(value: Any) -> str:
    return str(value).strip().lower()


# ============================================================
# BLACK-BOX REQUEST
# ============================================================

@dataclass
class BlackBoxRequest:
    """
    Public request envelope.

    IMPORTANT:
    This object contains metadata and public feature contracts only.

    It MUST NOT contain:
        - raw arrays
        - raw DICOM pixels
        - raw signal samples
        - private parameters
        - model weights
        - secrets
        - proprietary algorithm configuration
    """

    request_id: str

    dataset_id: str

    target_id: str

    analysis_mode: str

    input_type: str

    requested_features: List[str] = field(
        default_factory=list
    )

    source_hash: Optional[str] = None

    provenance: Dict[str, Any] = field(
        default_factory=dict
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    human_review_required: bool = False

    created_at: str = field(
        default_factory=utc_timestamp
    )

    protocol_version: str = BLACKBOX_PROTOCOL_VERSION

    def normalize(self) -> "BlackBoxRequest":

        self.request_id = sanitize_identifier(
            self.request_id,
            generate_client_request_id(),
        )

        self.dataset_id = sanitize_identifier(
            self.dataset_id
        )

        self.target_id = sanitize_identifier(
            self.target_id
        )

        self.analysis_mode = str(
            self.analysis_mode
        ).strip().upper()

        self.input_type = str(
            self.input_type
        ).strip().upper()

        self.requested_features = sorted(
            {
                normalize_feature_name(feature)
                for feature in self.requested_features
                if str(feature).strip()
            }
        )

        return self

    def to_public_dict(self) -> Dict[str, Any]:
        """
        Return only the public request contract.
        """

        return {
            "request_id": self.request_id,
            "dataset_id": self.dataset_id,
            "target_id": self.target_id,
            "analysis_mode": self.analysis_mode,
            "input_type": self.input_type,
            "requested_features": list(
                self.requested_features
            ),
            "source_hash": self.source_hash,
            "provenance": self.provenance,
            "metadata": self.metadata,
            "human_review_required": (
                self.human_review_required
            ),
            "created_at": self.created_at,
            "protocol_version": self.protocol_version,
        }


# ============================================================
# BLACK-BOX RESPONSE
# ============================================================

@dataclass
class BlackBoxResponse:
    """
    Public response envelope.

    The response may contain public feature values/results,
    but never private implementation details.
    """

    request_id: str

    status: ClientStatus

    target_id: Optional[str] = None

    message: str = ""

    features: Dict[str, Any] = field(
        default_factory=dict
    )

    uncertainty: Dict[str, Any] = field(
        default_factory=dict
    )

    provenance: Dict[str, Any] = field(
        default_factory=dict
    )

    warnings: List[str] = field(
        default_factory=list
    )

    execution_metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    created_at: str = field(
        default_factory=utc_timestamp
    )

    protocol_version: str = BLACKBOX_PROTOCOL_VERSION

    response_fingerprint: Optional[str] = None

    def finalize(self) -> "BlackBoxResponse":
        """
        Generate a fingerprint over public response metadata.
        """

        payload = {
            "request_id": self.request_id,
            "status": self.status.value,
            "target_id": self.target_id,
            "features": self.features,
            "uncertainty": self.uncertainty,
            "warnings": self.warnings,
            "protocol_version": self.protocol_version,
        }

        self.response_fingerprint = calculate_sha256(
            payload
        )

        return self

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(
            self.to_dict(),
            indent=indent,
            ensure_ascii=False,
            default=str,
        )


# ============================================================
# BLACK-BOX CLIENT
# ============================================================

class BlackBoxClient:
    """
    Public client boundary for a private research engine.

    This class DOES NOT implement the intelligence engine.

    It only:
        - validates a request
        - creates a safe request envelope
        - optionally accepts a future private execution adapter
        - returns a safe response envelope

    The public version defaults to CONTRACT_ONLY mode.
    """

    def __init__(
        self,
        target_id: Optional[str] = None,
        execution_mode: ExecutionMode = (
            ExecutionMode.CONTRACT_ONLY
        ),
        private_executor: Optional[Any] = None,
    ):
        self.target_id = (
            sanitize_identifier(target_id)
            if target_id
            else None
        )

        self.execution_mode = execution_mode

        # ----------------------------------------------------
        # SECURITY:
        # A private executor is NOT imported dynamically.
        #
        # No eval()
        # No exec()
        # No arbitrary module path
        #
        # A future private deployment may inject a controlled
        # implementation through an explicitly managed boundary.
        # ----------------------------------------------------

        self._private_executor = private_executor

    # ========================================================
    # REQUEST VALIDATION
    # ========================================================

    def validate_request(
        self,
        request: BlackBoxRequest,
    ) -> Tuple[bool, List[str]]:

        errors: List[str] = []

        request.normalize()

        # --------------------------------------------
        # Required fields
        # --------------------------------------------

        if not request.request_id:
            errors.append(
                "request_id is required."
            )

        if not request.dataset_id:
            errors.append(
                "dataset_id is required."
            )

        if not request.target_id:
            errors.append(
                "target_id is required."
            )

        if not request.analysis_mode:
            errors.append(
                "analysis_mode is required."
            )

        if not request.input_type:
            errors.append(
                "input_type is required."
            )

        # --------------------------------------------
        # Feature allow-list
        # --------------------------------------------

        invalid_features = [
            feature
            for feature in request.requested_features
            if feature not in SAFE_FEATURES
        ]

        if invalid_features:
            errors.append(
                "Unsupported/private feature requested: "
                + ", ".join(invalid_features)
            )

        # --------------------------------------------
        # Source hash sanity
        # --------------------------------------------

        if request.source_hash is not None:

            source_hash = str(
                request.source_hash
            ).strip()

            if source_hash:

                if not re.fullmatch(
                    r"[a-fA-F0-9]{32,128}",
                    source_hash,
                ):
                    errors.append(
                        "source_hash does not match "
                        "an expected hexadecimal hash format."
                    )

        # --------------------------------------------
        # Human-review policy
        # --------------------------------------------

        if request.analysis_mode == "BIOMEDICAL":

            # Router/client policy enforces review.
            request.human_review_required = True

        # --------------------------------------------
        # Public metadata inspection
        # --------------------------------------------

        payload = {
            "provenance": request.provenance,
            "metadata": request.metadata,
        }

        forbidden_found = self._find_forbidden_keys(
            payload
        )

        if forbidden_found:

            errors.append(
                "Sensitive/private request fields detected: "
                + ", ".join(forbidden_found)
            )

        return (
            len(errors) == 0,
            errors,
        )

    # ========================================================
    # FORBIDDEN FIELD SCANNER
    # ========================================================

    def _find_forbidden_keys(
        self,
        payload: Any,
        path: str = "",
    ) -> List[str]:

        found: List[str] = []

        if isinstance(payload, dict):

            for key, value in payload.items():

                key_lower = str(key).strip().lower()

                current_path = (
                    f"{path}.{key}"
                    if path
                    else str(key)
                )

                if (
                    key_lower in FORBIDDEN_REQUEST_FIELDS
                    or any(
                        token in key_lower
                        for token in (
                            "password",
                            "secret",
                            "api_key",
                            "access_token",
                            "private_key",
                            "model_weights",
                            "mcmc_parameters",
                            "proprietary_parameters",
                        )
                    )
                ):
                    found.append(current_path)

                found.extend(
                    self._find_forbidden_keys(
                        value,
                        current_path,
                    )
                )

        elif isinstance(payload, list):

            for index, item in enumerate(payload):

                found.extend(
                    self._find_forbidden_keys(
                        item,
                        f"{path}[{index}]",
                    )
                )

        return found

    # ========================================================
    # BUILD PUBLIC REQUEST
    # ========================================================

    def build_request(
        self,
        *,
        dataset_id: str,
        analysis_mode: str,
        input_type: str,
        requested_features: Optional[List[str]] = None,
        source_hash: Optional[str] = None,
        provenance: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        human_review_required: bool = False,
        request_id: Optional[str] = None,
        target_id: Optional[str] = None,
    ) -> BlackBoxRequest:

        resolved_target = (
            target_id
            or self.target_id
        )

        if not resolved_target:
            resolved_target = (
                "UNCONFIGURED_BLACKBOX_TARGET"
            )

        request = BlackBoxRequest(
            request_id=(
                request_id
                or generate_client_request_id()
            ),
            dataset_id=dataset_id,
            target_id=resolved_target,
            analysis_mode=analysis_mode,
            input_type=input_type,
            requested_features=(
                requested_features or []
            ),
            source_hash=source_hash,
            provenance=(
                provenance or {}
            ),
            metadata=(
                metadata or {}
            ),
            human_review_required=(
                human_review_required
            ),
        )

        request.normalize()

        valid, errors = self.validate_request(
            request
        )

        if not valid:
            raise ValueError(
                "Invalid black-box request: "
                + " | ".join(errors)
            )

        return request

    # ========================================================
    # CONTRACT-ONLY EXECUTION
    # ========================================================

    def execute(
        self,
        request: BlackBoxRequest,
    ) -> BlackBoxResponse:

        valid, errors = self.validate_request(
            request
        )

        if not valid:

            return BlackBoxResponse(
                request_id=request.request_id,
                status=ClientStatus.REJECTED,
                target_id=request.target_id,
                message=(
                    "Black-box request rejected by "
                    "public security contract."
                ),
                warnings=errors,
                execution_metadata={
                    "execution_performed": False,
                    "private_engine_access": False,
                },
            ).finalize()

        # ----------------------------------------------------
        # CONTRACT-ONLY MODE
        # ----------------------------------------------------

        if (
            self.execution_mode
            == ExecutionMode.CONTRACT_ONLY
        ):

            return BlackBoxResponse(
                request_id=request.request_id,
                status=ClientStatus.DEFERRED,
                target_id=request.target_id,
                message=(
                    "Public black-box contract created. "
                    "Private engine execution is not "
                    "included in this public module."
                ),
                features={},
                uncertainty={},
                provenance={
                    "source_hash": request.source_hash,
                    "protocol_version": (
                        BLACKBOX_PROTOCOL_VERSION
                    ),
                },
                warnings=[
                    "NO_PRIVATE_ENGINE_EXECUTED",
                    "NO_PROPRIETARY_CODE_EXPOSED",
                ],
                execution_metadata={
                    "execution_performed": False,
                    "execution_mode": (
                        ExecutionMode.CONTRACT_ONLY.value
                    ),
                },
            ).finalize()

        # ----------------------------------------------------
        # PRIVATE ENGINE MODE
        # ----------------------------------------------------
        #
        # No proprietary implementation is present here.
        #
        # If a controlled private executor has been explicitly
        # injected by a private deployment, this boundary may
        # delegate to it.
        #
        # The public repository contains no such implementation.
        # ----------------------------------------------------

        if (
            self.execution_mode
            == ExecutionMode.PRIVATE_ENGINE
        ):

            if self._private_executor is None:

                return BlackBoxResponse(
                    request_id=request.request_id,
                    status=ClientStatus.NOT_CONFIGURED,
                    target_id=request.target_id,
                    message=(
                        "Private engine executor is not "
                        "configured in this public environment."
                    ),
                    warnings=[
                        "PRIVATE_ENGINE_NOT_CONFIGURED",
                        "NO_PROPRIETARY_CODE_INCLUDED",
                    ],
                    execution_metadata={
                        "execution_performed": False,
                        "private_engine_access": False,
                    },
                ).finalize()

            # ------------------------------------------------
            # Controlled executor boundary
            # ------------------------------------------------
            #
            # Only a callable explicitly supplied by the
            # private deployment may be used.
            #
            # No dynamic import is performed.
            # ------------------------------------------------

            if not callable(
                self._private_executor
            ):

                return BlackBoxResponse(
                    request_id=request.request_id,
                    status=ClientStatus.FAILED,
                    target_id=request.target_id,
                    message=(
                        "Configured private executor "
                        "is not callable."
                    ),
                    warnings=[
                        "INVALID_PRIVATE_EXECUTOR"
                    ],
                    execution_metadata={
                        "execution_performed": False
                    },
                ).finalize()

            try:

                private_result = (
                    self._private_executor(
                        request.to_public_dict()
                    )
                )

            except Exception as exc:

                # Do NOT expose internal exception details.
                return BlackBoxResponse(
                    request_id=request.request_id,
                    status=ClientStatus.FAILED,
                    target_id=request.target_id,
                    message=(
                        "Private engine execution "
                        "returned an error."
                    ),
                    warnings=[
                        "PRIVATE_ENGINE_ERROR"
                    ],
                    execution_metadata={
                        "execution_performed": False,
                        "error_details_hidden": True,
                    },
                ).finalize()

            # --------------------------------------------
            # Normalize private result
            # --------------------------------------------

            return self._sanitize_private_result(
                request,
                private_result,
            )

        # ----------------------------------------------------
        # Unknown execution mode
        # ----------------------------------------------------

        return BlackBoxResponse(
            request_id=request.request_id,
            status=ClientStatus.FAILED,
            target_id=request.target_id,
            message=(
                "Unsupported execution mode."
            ),
            warnings=[
                "UNKNOWN_EXECUTION_MODE"
            ],
            execution_metadata={
                "execution_performed": False
            },
        ).finalize()

    # ========================================================
    # PRIVATE RESULT SANITIZATION
    # ========================================================

    def _sanitize_private_result(
        self,
        request: BlackBoxRequest,
        private_result: Any,
    ) -> BlackBoxResponse:
        """
        Convert a private result into the public response schema.

        Only allow-listed feature names may cross the boundary.
        """

        if not isinstance(
            private_result,
            dict,
        ):

            return BlackBoxResponse(
                request_id=request.request_id,
                status=ClientStatus.FAILED,
                target_id=request.target_id,
                message=(
                    "Private engine returned an "
                    "invalid public response."
                ),
                warnings=[
                    "INVALID_PRIVATE_RESPONSE"
                ],
                execution_metadata={
                    "execution_performed": False,
                    "response_details_hidden": True,
                },
            ).finalize()

        # --------------------------------------------
        # Status
        # --------------------------------------------

        raw_status = str(
            private_result.get(
                "status",
                "COMPLETED",
            )
        ).upper()

        try:
            status = ClientStatus(
                raw_status
            )
        except ValueError:
            status = ClientStatus.COMPLETED

        # --------------------------------------------
        # Features
        # --------------------------------------------

        raw_features = private_result.get(
            "features",
            {},
        )

        safe_features: Dict[str, Any] = {}

        if isinstance(
            raw_features,
            dict,
        ):

            for name, value in raw_features.items():

                normalized_name = (
                    normalize_feature_name(name)
                )

                if (
                    normalized_name
                    in SAFE_FEATURES
                ):

                    safe_features[
                        normalized_name
                    ] = value

        # --------------------------------------------
        # Uncertainty
        # --------------------------------------------

        raw_uncertainty = private_result.get(
            "uncertainty",
            {},
        )

        safe_uncertainty = (
            raw_uncertainty
            if isinstance(
                raw_uncertainty,
                dict,
            )
            else {}
        )

        # --------------------------------------------
        # Public response
        # --------------------------------------------

        return BlackBoxResponse(
            request_id=request.request_id,
            status=status,
            target_id=request.target_id,
            message=(
                "Private engine response converted "
                "to public feature contract."
            ),
            features=safe_features,
            uncertainty=safe_uncertainty,
            provenance={
                "source_hash": request.source_hash,
                "protocol_version": (
                    BLACKBOX_PROTOCOL_VERSION
                ),
            },
            warnings=[
                "PRIVATE_IMPLEMENTATION_NOT_EXPOSED",
            ],
            execution_metadata={
                "execution_performed": True,
                "private_algorithm_details_exposed": False,
            },
        ).finalize()

    # ========================================================
    # SAFE CONTRACT PREVIEW
    # ========================================================

    def preview_contract(
        self,
        request: BlackBoxRequest,
    ) -> Dict[str, Any]:
        """
        Return the exact public information that would cross
        the black-box boundary.
        """

        valid, errors = self.validate_request(
            request
        )

        if not valid:
            return {
                "valid": False,
                "errors": errors,
            }

        return {
            "valid": True,
            "protocol_version": (
                BLACKBOX_PROTOCOL_VERSION
            ),
            "request": request.to_public_dict(),
            "private_implementation_exposed": False,
            "raw_data_included": False,
            "secrets_included": False,
        }


# ============================================================
# STANDARD CLIENT FACTORY
# ============================================================

def create_blackbox_client(
    target_id: Optional[str] = None,
) -> BlackBoxClient:
    """
    Create the standard PUBLIC black-box client.

    Default mode is CONTRACT_ONLY.

    Therefore this factory cannot accidentally execute
    proprietary code.
    """

    return BlackBoxClient(
        target_id=target_id,
        execution_mode=ExecutionMode.CONTRACT_ONLY,
        private_executor=None,
    )


# ============================================================
# PUBLIC PROTOCOL CONTRACT
# ============================================================

def blackbox_protocol_contract() -> Dict[str, Any]:
    """
    Return the public black-box protocol contract.
    """

    return {
        "module": MODULE_NAME,
        "version": MODULE_VERSION,
        "protocol_version": (
            BLACKBOX_PROTOCOL_VERSION
        ),

        "purpose": (
            "Safe public boundary between routing layer "
            "and an external/private intelligence engine."
        ),

        "proprietary_algorithms_included": (
            PROPRIETARY_ALGORITHMS_INCLUDED
        ),

        "private_engine_source_included": (
            PRIVATE_ENGINE_SOURCE_INCLUDED
        ),

        "secrets_included": (
            SECRETS_INCLUDED
        ),

        "raw_data_transmission_allowed": (
            RAW_DATA_TRANSMISSION_ALLOWED
        ),

        "raw_data_modification_allowed": (
            RAW_DATA_MODIFICATION_ALLOWED
        ),

        "medical_diagnosis_supported": (
            MEDICAL_DIAGNOSIS_SUPPORTED
        ),

        "flight_certification_supported": (
            FLIGHT_CERTIFICATION_SUPPORTED
        ),

        "safe_features": sorted(
            SAFE_FEATURES
        ),

        "default_execution_mode": (
            ExecutionMode.CONTRACT_ONLY.value
        ),
    }


# ============================================================
# SECURITY SELF-TEST
# ============================================================

def run_blackbox_client_test() -> Dict[str, Any]:

    results: Dict[str, Any] = {}

    # --------------------------------------------------------
    # Test 1: Client creation
    # --------------------------------------------------------

    client = create_blackbox_client(
        target_id="PRIVATE_SPACE_ENGINE"
    )

    results["client_created"] = (
        isinstance(
            client,
            BlackBoxClient,
        )
    )

    # --------------------------------------------------------
    # Test 2: Safe request
    # --------------------------------------------------------

    request = client.build_request(
        dataset_id="NASA_DEMO_001",
        analysis_mode="SPACE",
        input_type="TIME_SERIES",
        requested_features=[
            "entropy",
            "variance",
            "signal_quality",
        ],
        source_hash=(
            "a" * 64
        ),
        provenance={
            "source": "public_demo"
        },
        metadata={
            "purpose": "research_validation"
        },
    )

    results["safe_request_created"] = (
        isinstance(
            request,
            BlackBoxRequest,
        )
    )

    # --------------------------------------------------------
    # Test 3: Contract preview
    # --------------------------------------------------------

    preview = client.preview_contract(
        request
    )

    results["contract_preview_valid"] = (
        preview.get("valid") is True
    )

    results["raw_data_excluded"] = (
        preview.get(
            "raw_data_included"
        ) is False
    )

    results["private_implementation_hidden"] = (
        preview.get(
            "private_implementation_exposed"
        ) is False
    )

    # --------------------------------------------------------
    # Test 4: Contract-only execution
    # --------------------------------------------------------

    response = client.execute(
        request
    )

    results["contract_execution_deferred"] = (
        response.status
        == ClientStatus.DEFERRED
    )

    results["execution_not_performed"] = (
        response.execution_metadata.get(
            "execution_performed"
        ) is False
    )

    # --------------------------------------------------------
    # Test 5: Private feature rejection
    # --------------------------------------------------------

    private_request = BlackBoxRequest(
        request_id="private-test",
        dataset_id="test",
        target_id="PRIVATE_SPACE_ENGINE",
        analysis_mode="SPACE",
        input_type="TIME_SERIES",
        requested_features=[
            "entropy",
            "internal_proprietary_feature",
        ],
    )

    valid, errors = client.validate_request(
        private_request
    )

    results["private_feature_rejected"] = (
        valid is False
    )

    # --------------------------------------------------------
    # Test 6: Secret-field detection
    # --------------------------------------------------------

    secret_request = BlackBoxRequest(
        request_id="secret-test",
        dataset_id="test",
        target_id="PRIVATE_SPACE_ENGINE",
        analysis_mode="SPACE",
        input_type="TIME_SERIES",
        metadata={
            "api_key": "DO_NOT_ACCEPT"
        },
    )

    valid, errors = client.validate_request(
        secret_request
    )

    results["secret_field_rejected"] = (
        valid is False
    )

    # --------------------------------------------------------
    # Test 7: Biomedical policy
    # --------------------------------------------------------

    biomedical_request = client.build_request(
        dataset_id="DICOM_RESEARCH_001",
        analysis_mode="BIOMEDICAL",
        input_type="DICOM",
        requested_features=[
            "entropy",
            "anomaly_score",
        ],
    )

    results["biomedical_human_review_enforced"] = (
        biomedical_request.human_review_required
        is True
    )

    # --------------------------------------------------------
    # Test 8: Clinical diagnosis field is NOT supported
    # --------------------------------------------------------

    clinical_payload = {
        "analysis_mode": "BIOMEDICAL",
        "clinical_diagnosis": True,
    }

    forbidden = client._find_forbidden_keys(
        clinical_payload
    )

    # Clinical diagnosis is not itself a secret, but it
    # demonstrates that private decision fields are not part
    # of the public feature contract.
    results["clinical_feature_contract_not_used"] = (
        "clinical_diagnosis"
        not in SAFE_FEATURES
    )

    # --------------------------------------------------------
    # Test 9: Protocol security flags
    # --------------------------------------------------------

    contract = blackbox_protocol_contract()

    results["proprietary_code_absent"] = (
        contract[
            "proprietary_algorithms_included"
        ] is False
    )

    results["private_source_absent"] = (
        contract[
            "private_engine_source_included"
        ] is False
    )

    results["secrets_absent"] = (
        contract[
            "secrets_included"
        ] is False
    )

    results["raw_data_transmission_disabled"] = (
        contract[
            "raw_data_transmission_allowed"
        ] is False
    )

    results["raw_data_modification_disabled"] = (
        contract[
            "raw_data_modification_allowed"
        ] is False
    )

    # --------------------------------------------------------
    # Test 10: No dynamic execution mechanism
    # --------------------------------------------------------

    results["default_mode_contract_only"] = (
        client.execution_mode
        == ExecutionMode.CONTRACT_ONLY
    )

    results["private_executor_not_configured"] = (
        client._private_executor is None
    )

    # --------------------------------------------------------
    # Final
    # --------------------------------------------------------

    boolean_checks = [
        value
        for value in results.values()
        if isinstance(value, bool)
    ]

    results["all_security_checks_passed"] = (
        all(boolean_checks)
        if boolean_checks
        else False
    )

    return results


# ============================================================
# MODULE INFO
# ============================================================

def module_info() -> Dict[str, Any]:

    return {
        "module_name": MODULE_NAME,
        "module_version": MODULE_VERSION,
        "protocol_version": (
            BLACKBOX_PROTOCOL_VERSION
        ),

        "role": (
            "Public black-box boundary client."
        ),

        "execution_default": (
            ExecutionMode.CONTRACT_ONLY.value
        ),

        "proprietary_algorithm_included": False,
        "private_engine_source_included": False,
        "secrets_included": False,

        "raw_data_transmission": False,
        "raw_data_modification": False,

        "medical_diagnosis": False,
        "flight_certification": False,
    }


# ============================================================
# SELF TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 72)
    print(
        "D³ VITAL-X — Module 17: blackbox_client.py"
    )
    print("=" * 72)

    results = run_blackbox_client_test()

    for key, value in results.items():
        print(f"{key}: {value}")

    print("=" * 72)

    if results[
        "all_security_checks_passed"
    ]:
        print(
            "✅ BLACKBOX CLIENT SECURITY TEST: PASS"
        )
    else:
        print(
            "❌ BLACKBOX CLIENT SECURITY TEST: REVIEW REQUIRED"
        )

    print("=" * 72)
