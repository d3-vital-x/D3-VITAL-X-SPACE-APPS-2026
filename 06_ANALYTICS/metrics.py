# ============================================================
# D³ VITAL-X Space Intelligence Platform
# Module 18 — metrics.py
# ============================================================
#
# PUBLIC ANALYTICS OUTPUT LAYER
#
# ============================================================
# SECURITY / ARCHITECTURE PRINCIPLES
# ============================================================
#
# This module is intentionally a PUBLIC result-processing layer.
#
# It DOES NOT contain:
#
#   ❌ v10 source code
#   ❌ v11 source code
#   ❌ UTL/DVDH implementation
#   ❌ DSI calculation
#   ❌ Effective Mass calculation
#   ❌ PLV calculation
#   ❌ Lyapunov calculation
#   ❌ RQA calculation
#   ❌ proprietary coupling equations
#   ❌ MCMC implementation
#   ❌ proprietary coefficients
#   ❌ model weights
#   ❌ private endpoints
#   ❌ API keys / secrets
#   ❌ clinical diagnosis
#
# It ONLY:
#
#   1. accepts public metric values
#   2. validates numerical values
#   3. records provenance
#   4. assigns public quality states
#   5. summarizes metric collections
#   6. preserves claim-classification boundaries
#
# IMPORTANT:
# A metric value supplied by a private engine is treated as
# an OBSERVED/RETURNED RESULT. This module does not infer
# the proprietary algorithm that generated it.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import hashlib
import json
import math
import uuid


# ============================================================
# MODULE METADATA
# ============================================================

MODULE_NAME = "metrics"
MODULE_VERSION = "1.0.0"
METRICS_SCHEMA_VERSION = "1.0"

PROPRIETARY_ALGORITHMS_INCLUDED = False
RAW_DATA_MODIFICATION_ALLOWED = False
MEDICAL_DIAGNOSIS_SUPPORTED = False
FLIGHT_CERTIFICATION_SUPPORTED = False


# ============================================================
# ENUMS
# ============================================================

class MetricCategory(str, Enum):
    """
    Public metric categories.

    These are descriptive categories only.
    They do not define the proprietary calculation.
    """

    SIGNAL = "SIGNAL"
    STATISTICAL = "STATISTICAL"
    ENTROPY = "ENTROPY"
    VARIANCE = "VARIANCE"
    GRADIENT = "GRADIENT"
    COUPLING = "COUPLING"
    TRANSITION = "TRANSITION"
    ANOMALY = "ANOMALY"
    QUALITY = "QUALITY"
    UNCERTAINTY = "UNCERTAINTY"
    TEMPORAL = "TEMPORAL"
    SPECTRAL = "SPECTRAL"
    SPATIAL = "SPATIAL"
    CUSTOM = "CUSTOM"


class MetricValueType(str, Enum):
    SCALAR = "SCALAR"
    VECTOR = "VECTOR"
    SERIES = "SERIES"
    MATRIX = "MATRIX"
    BOOLEAN = "BOOLEAN"
    CATEGORICAL = "CATEGORICAL"
    TEXT = "TEXT"
    NULL = "NULL"


class MetricQuality(str, Enum):
    """
    Public quality state.

    This is NOT a scientific significance judgment.
    """

    VALID = "VALID"
    INVALID = "INVALID"
    MISSING = "MISSING"
    NONFINITE = "NONFINITE"
    LOW_QUALITY = "LOW_QUALITY"
    UNVERIFIED = "UNVERIFIED"


class ClaimClass(str, Enum):
    """
    Public evidence/claim classification.

    C1 = directly measured / directly supplied observation
    C2 = computationally derived public result
    C3 = hypothesis / interpretation / future application
    """

    C1 = "C1"
    C2 = "C2"
    C3 = "C3"


# ============================================================
# SAFE UTILITIES
# ============================================================

def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_metric_id() -> str:
    return f"metric-{uuid.uuid4().hex}"


def canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )


def calculate_sha256(payload: Any) -> str:
    return hashlib.sha256(
        canonical_json(payload).encode("utf-8")
    ).hexdigest()


def is_finite_number(value: Any) -> bool:
    """
    Return True only for finite int/float-like scalar values.

    Booleans are explicitly excluded.
    """

    if isinstance(value, bool):
        return False

    if not isinstance(value, (int, float)):
        return False

    return math.isfinite(float(value))


def safe_float(value: Any) -> Optional[float]:
    if not is_finite_number(value):
        return None

    return float(value)


def sanitize_identifier(
    value: Any,
    fallback: str = "unknown",
) -> str:

    if value is None:
        return fallback

    text = str(value).strip()

    if not text:
        return fallback

    return text[:128]


def infer_value_type(value: Any) -> MetricValueType:

    if value is None:
        return MetricValueType.NULL

    if isinstance(value, bool):
        return MetricValueType.BOOLEAN

    if is_finite_number(value):
        return MetricValueType.SCALAR

    if isinstance(value, str):
        return MetricValueType.TEXT

    if isinstance(value, (list, tuple)):

        if all(
            is_finite_number(item)
            for item in value
        ):
            return MetricValueType.VECTOR

        return MetricValueType.SERIES

    if isinstance(value, dict):
        return MetricValueType.CATEGORICAL

    return MetricValueType.CATEGORICAL


# ============================================================
# METRIC DEFINITION
# ============================================================

@dataclass(frozen=True)
class MetricDefinition:
    """
    Public metadata describing a metric.

    It does NOT describe the proprietary equation.
    """

    name: str

    category: MetricCategory

    value_type: MetricValueType

    unit: Optional[str] = None

    description: str = ""

    claim_class: ClaimClass = ClaimClass.C2

    human_review_required: bool = False

    nullable: bool = True

    version: str = "1.0"

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def validate(self) -> Tuple[bool, List[str]]:

        errors: List[str] = []

        if not self.name:
            errors.append(
                "Metric name is required."
            )

        if not isinstance(
            self.category,
            MetricCategory,
        ):
            errors.append(
                "Invalid metric category."
            )

        if not isinstance(
            self.value_type,
            MetricValueType,
        ):
            errors.append(
                "Invalid metric value type."
            )

        if not isinstance(
            self.claim_class,
            ClaimClass,
        ):
            errors.append(
                "Invalid claim class."
            )

        return (
            len(errors) == 0,
            errors,
        )


# ============================================================
# METRIC VALUE
# ============================================================

@dataclass
class MetricValue:
    """
    Public metric result.

    This object stores the result, not the algorithm that
    produced it.
    """

    metric_id: str

    definition: MetricDefinition

    value: Any = None

    quality: MetricQuality = MetricQuality.UNVERIFIED

    confidence: Optional[float] = None

    uncertainty: Optional[Any] = None

    source_dataset_id: Optional[str] = None

    source_hash: Optional[str] = None

    provenance: Dict[str, Any] = field(
        default_factory=dict
    )

    timestamp: str = field(
        default_factory=utc_timestamp
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def validate(self) -> Tuple[bool, List[str]]:

        errors: List[str] = []

        definition_valid, definition_errors = (
            self.definition.validate()
        )

        if not definition_valid:
            errors.extend(
                definition_errors
            )

        if not self.metric_id:
            errors.append(
                "metric_id is required."
            )

        # ----------------------------------------------------
        # Missing value
        # ----------------------------------------------------

        if self.value is None:

            if not self.definition.nullable:

                errors.append(
                    f"Metric '{self.definition.name}' "
                    "does not allow null values."
                )

            return (
                len(errors) == 0,
                errors,
            )

        # ----------------------------------------------------
        # Scalar validation
        # ----------------------------------------------------

        if (
            self.definition.value_type
            == MetricValueType.SCALAR
        ):

            if not is_finite_number(
                self.value
            ):
                errors.append(
                    f"Metric '{self.definition.name}' "
                    "contains a non-finite scalar."
                )

            if self.definition.name.lower() == "confidence":
                if not (0.0 <= float(self.value) <= 1.0):
                    errors.append(
                        "Confidence metric value must be between 0 and 1."
                    )

        # ----------------------------------------------------
        # Confidence validation
        # ----------------------------------------------------

        if self.confidence is not None:

            if not is_finite_number(
                self.confidence
            ):

                errors.append(
                    "Confidence must be finite."
                )

            elif not (
                0.0
                <= float(self.confidence)
                <= 1.0
            ):

                errors.append(
                    "Confidence must be between "
                    "0 and 1."
                )

        return (
            len(errors) == 0,
            errors,
        )

    def evaluate_quality(self) -> MetricQuality:

        if self.value is None:
            self.quality = MetricQuality.MISSING
            return self.quality

        if (
            self.definition.value_type
            == MetricValueType.SCALAR
        ):

            if not is_finite_number(
                self.value
            ):
                self.quality = (
                    MetricQuality.NONFINITE
                )
                return self.quality

            if self.definition.name.lower() == "confidence":
                if not (0.0 <= float(self.value) <= 1.0):
                    self.quality = MetricQuality.INVALID
                    return self.quality

        if self.confidence is not None:

            if not is_finite_number(
                self.confidence
            ):

                self.quality = (
                    MetricQuality.INVALID
                )
                return self.quality

            if not (
                0.0
                <= float(self.confidence)
                <= 1.0
            ):

                self.quality = (
                    MetricQuality.INVALID
                )
                return self.quality

        self.quality = MetricQuality.VALID

        return self.quality

    def fingerprint(self) -> str:

        payload = {
            "metric_id": self.metric_id,
            "name": self.definition.name,
            "category": self.definition.category.value,
            "value_type": self.definition.value_type.value,
            "value": self.value,
            "quality": self.quality.value,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "source_dataset_id": self.source_dataset_id,
            "source_hash": self.source_hash,
        }

        return calculate_sha256(payload)

    def to_dict(self) -> Dict[str, Any]:

        result = asdict(self)

        result["definition"]["category"] = (
            self.definition.category.value
        )

        result["definition"]["value_type"] = (
            self.definition.value_type.value
        )

        result["definition"]["claim_class"] = (
            self.definition.claim_class.value
        )

        result["quality"] = self.quality.value

        return result


# ============================================================
# METRIC SET
# ============================================================

@dataclass
class MetricSet:
    """
    Collection of public metrics belonging to one analysis.
    """

    set_id: str

    dataset_id: str

    metrics: List[MetricValue] = field(
        default_factory=list
    )

    schema_version: str = (
        METRICS_SCHEMA_VERSION
    )

    created_at: str = field(
        default_factory=utc_timestamp
    )

    provenance: Dict[str, Any] = field(
        default_factory=dict
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def validate(self) -> Tuple[bool, List[str]]:

        errors: List[str] = []

        if not self.set_id:
            errors.append(
                "set_id is required."
            )

        if not self.dataset_id:
            errors.append(
                "dataset_id is required."
            )

        seen_names = set()

        for metric in self.metrics:

            valid, metric_errors = (
                metric.validate()
            )

            if not valid:
                errors.extend(
                    metric_errors
                )

            name = metric.definition.name

            if name in seen_names:
                errors.append(
                    f"Duplicate metric name: {name}"
                )

            seen_names.add(name)

        return (
            len(errors) == 0,
            errors,
        )

    def evaluate_quality(self) -> None:

        for metric in self.metrics:
            metric.evaluate_quality()

    def get(
        self,
        name: str,
    ) -> Optional[MetricValue]:

        name = str(name).strip().lower()

        for metric in self.metrics:

            if (
                metric.definition.name.lower()
                == name
            ):
                return metric

        return None

    def names(self) -> List[str]:

        return [
            metric.definition.name
            for metric in self.metrics
        ]

    def quality_summary(self) -> Dict[str, int]:

        summary = {
            quality.value: 0
            for quality in MetricQuality
        }

        for metric in self.metrics:
            summary[
                metric.quality.value
            ] += 1

        return summary

    def claim_class_summary(self) -> Dict[str, int]:

        summary = {
            claim.value: 0
            for claim in ClaimClass
        }

        for metric in self.metrics:
            summary[
                metric.definition.claim_class.value
            ] += 1

        return summary

    def fingerprint(self) -> str:

        payload = {
            "set_id": self.set_id,
            "dataset_id": self.dataset_id,
            "schema_version": self.schema_version,
            "metrics": [
                metric.fingerprint()
                for metric in self.metrics
            ],
        }

        return calculate_sha256(payload)

    def to_dict(self) -> Dict[str, Any]:

        return {
            "set_id": self.set_id,
            "dataset_id": self.dataset_id,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "provenance": self.provenance,
            "metadata": self.metadata,
            "metrics": [
                metric.to_dict()
                for metric in self.metrics
            ],
            "quality_summary": (
                self.quality_summary()
            ),
            "claim_class_summary": (
                self.claim_class_summary()
            ),
            "fingerprint": self.fingerprint(),
        }

    def to_json(
        self,
        indent: int = 2,
    ) -> str:

        return json.dumps(
            self.to_dict(),
            indent=indent,
            ensure_ascii=False,
            default=str,
        )


# ============================================================
# STANDARD METRIC REGISTRY
# ============================================================

class MetricRegistry:

    def __init__(self):

        self._definitions: Dict[
            str,
            MetricDefinition,
        ] = {}

    def register(
        self,
        definition: MetricDefinition,
    ) -> None:

        valid, errors = (
            definition.validate()
        )

        if not valid:

            raise ValueError(
                "Invalid metric definition: "
                + " | ".join(errors)
            )

        key = definition.name.lower()

        if key in self._definitions:

            raise ValueError(
                f"Metric already registered: "
                f"{definition.name}"
            )

        self._definitions[key] = (
            definition
        )

    def get(
        self,
        name: str,
    ) -> Optional[MetricDefinition]:

        return self._definitions.get(
            str(name).strip().lower()
        )

    def names(self) -> List[str]:

        return sorted(
            self._definitions.keys()
        )

    def definitions(self) -> List[MetricDefinition]:

        return list(
            self._definitions.values()
        )


def create_standard_metric_registry() -> MetricRegistry:
    """
    Create the public metric registry.

    These are interface-level metric names.
    No proprietary equations are included.
    """

    registry = MetricRegistry()

    registry.register(
        MetricDefinition(
            name="entropy",
            category=MetricCategory.ENTROPY,
            value_type=MetricValueType.SCALAR,
            description=(
                "Public entropy-related metric returned "
                "by an analysis component."
            ),
            claim_class=ClaimClass.C2,
        )
    )

    registry.register(
        MetricDefinition(
            name="variance",
            category=MetricCategory.VARIANCE,
            value_type=MetricValueType.SCALAR,
            description=(
                "Public variance-related metric."
            ),
            claim_class=ClaimClass.C2,
        )
    )

    registry.register(
        MetricDefinition(
            name="gradient",
            category=MetricCategory.GRADIENT,
            value_type=MetricValueType.SCALAR,
            description=(
                "Public gradient-related metric."
            ),
            claim_class=ClaimClass.C2,
        )
    )

    registry.register(
        MetricDefinition(
            name="coupling",
            category=MetricCategory.COUPLING,
            value_type=MetricValueType.SCALAR,
            description=(
                "Public coupling metric supplied by "
                "an analysis component."
            ),
            claim_class=ClaimClass.C2,
        )
    )

    registry.register(
        MetricDefinition(
            name="transition_index",
            category=MetricCategory.TRANSITION,
            value_type=MetricValueType.SCALAR,
            description=(
                "Public transition-related index."
            ),
            claim_class=ClaimClass.C2,
            human_review_required=True,
        )
    )

    registry.register(
        MetricDefinition(
            name="anomaly_score",
            category=MetricCategory.ANOMALY,
            value_type=MetricValueType.SCALAR,
            description=(
                "Research anomaly-prioritization score; "
                "not a diagnosis."
            ),
            claim_class=ClaimClass.C2,
            human_review_required=True,
        )
    )

    registry.register(
        MetricDefinition(
            name="signal_quality",
            category=MetricCategory.QUALITY,
            value_type=MetricValueType.SCALAR,
            description=(
                "Public signal or image quality indicator."
            ),
            claim_class=ClaimClass.C2,
        )
    )

    registry.register(
        MetricDefinition(
            name="confidence",
            category=MetricCategory.QUALITY,
            value_type=MetricValueType.SCALAR,
            description=(
                "Public confidence value associated with "
                "a computational result."
            ),
            claim_class=ClaimClass.C2,
        )
    )

    registry.register(
        MetricDefinition(
            name="uncertainty",
            category=MetricCategory.UNCERTAINTY,
            value_type=MetricValueType.SCALAR,
            description=(
                "Public uncertainty estimate supplied by "
                "an analysis component."
            ),
            claim_class=ClaimClass.C2,
        )
    )

    return registry


# ============================================================
# METRIC CREATION
# ============================================================

def create_metric(
    registry: MetricRegistry,
    name: str,
    value: Any = None,
    *,
    confidence: Optional[float] = None,
    uncertainty: Optional[Any] = None,
    source_dataset_id: Optional[str] = None,
    source_hash: Optional[str] = None,
    provenance: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> MetricValue:

    definition = registry.get(name)

    if definition is None:

        raise ValueError(
            f"Unknown public metric: {name}"
        )

    metric = MetricValue(
        metric_id=generate_metric_id(),
        definition=definition,
        value=value,
        confidence=confidence,
        uncertainty=uncertainty,
        source_dataset_id=(
            sanitize_identifier(
                source_dataset_id
            )
            if source_dataset_id
            else None
        ),
        source_hash=source_hash,
        provenance=(
            provenance or {}
        ),
        metadata=(
            metadata or {}
        ),
    )

    metric.evaluate_quality()

    return metric


# ============================================================
# METRIC SET CREATION
# ============================================================

def create_metric_set(
    dataset_id: str,
    metrics: Optional[List[MetricValue]] = None,
    *,
    provenance: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> MetricSet:

    metric_set = MetricSet(
        set_id=f"metric-set-{uuid.uuid4().hex}",
        dataset_id=sanitize_identifier(
            dataset_id
        ),
        metrics=metrics or [],
        provenance=(
            provenance or {}
        ),
        metadata=(
            metadata or {}
        ),
    )

    metric_set.evaluate_quality()

    return metric_set


# ============================================================
# SAFE SUMMARY FUNCTIONS
# ============================================================

def summarize_metric_set(
    metric_set: MetricSet,
) -> Dict[str, Any]:

    metric_set.evaluate_quality()

    numeric_values: Dict[
        str,
        float,
    ] = {}

    for metric in metric_set.metrics:

        if (
            metric.definition.value_type
            == MetricValueType.SCALAR
            and is_finite_number(metric.value)
        ):

            numeric_values[
                metric.definition.name
            ] = float(metric.value)

    return {
        "dataset_id": metric_set.dataset_id,
        "metric_count": len(
            metric_set.metrics
        ),
        "numeric_metric_count": len(
            numeric_values
        ),
        "metric_names": metric_set.names(),
        "quality_summary": (
            metric_set.quality_summary()
        ),
        "claim_class_summary": (
            metric_set.claim_class_summary()
        ),
        "numeric_values": numeric_values,
        "fingerprint": (
            metric_set.fingerprint()
        ),
    }


# ============================================================
# PUBLIC PAYLOAD VALIDATION
# ============================================================

def validate_metric_payload(
    payload: Dict[str, Any],
    registry: Optional[MetricRegistry] = None,
) -> Tuple[bool, List[str]]:

    if registry is None:
        registry = (
            create_standard_metric_registry()
        )

    errors: List[str] = []

    if not isinstance(
        payload,
        dict,
    ):
        return (
            False,
            ["Metric payload must be a dictionary."],
        )

    name = payload.get("name")

    if not name:
        errors.append(
            "Metric payload requires 'name'."
        )
        return False, errors

    definition = registry.get(name)

    if definition is None:
        errors.append(
            f"Unknown metric: {name}"
        )
        return False, errors

    value = payload.get(
        "value"
    )

    if (
        definition.value_type
        == MetricValueType.SCALAR
    ):

        if value is not None and not is_finite_number(
            value
        ):

            errors.append(
                f"Metric '{name}' requires "
                "a finite scalar."
            )

        if definition.name.lower() == "confidence" and value is not None:
            if not (0.0 <= float(value) <= 1.0):
                errors.append("Confidence metric value must be between 0 and 1.")

    confidence = payload.get(
        "confidence"
    )

    if confidence is not None:

        if not is_finite_number(
            confidence
        ):

            errors.append(
                "Confidence must be finite."
            )

        elif not (
            0.0
            <= float(confidence)
            <= 1.0
        ):

            errors.append(
                "Confidence must be between 0 and 1."
            )

    return (
        len(errors) == 0,
        errors,
    )


# ============================================================
# PUBLIC METRIC CONTRACT
# ============================================================

def metrics_contract() -> Dict[str, Any]:

    registry = (
        create_standard_metric_registry()
    )

    return {
        "module": MODULE_NAME,
        "version": MODULE_VERSION,
        "schema_version": (
            METRICS_SCHEMA_VERSION
        ),

        "purpose": (
            "Public analytics result validation, "
            "quality assessment, and summarization."
        ),

        "proprietary_algorithms_included": (
            PROPRIETARY_ALGORITHMS_INCLUDED
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

        "registered_metrics": registry.names(),

        "calculation_policy": (
            "Metric values are accepted as public results; "
            "proprietary generation algorithms are not "
            "implemented in this module."
        ),
    }


# ============================================================
# SECURITY / ARCHITECTURE SELF-TEST
# ============================================================

def run_metrics_test() -> Dict[str, Any]:

    results: Dict[str, Any] = {}

    # --------------------------------------------------------
    # Registry
    # --------------------------------------------------------

    registry = (
        create_standard_metric_registry()
    )

    results["registry_created"] = (
        isinstance(
            registry,
            MetricRegistry,
        )
    )

    results["standard_metric_count"] = (
        len(registry.names())
    )

    # --------------------------------------------------------
    # Basic metric
    # --------------------------------------------------------

    entropy = create_metric(
        registry,
        "entropy",
        1.234,
        confidence=0.95,
        source_dataset_id="TEST_DATASET",
        source_hash="a" * 64,
    )

    results["entropy_created"] = (
        entropy.quality
        == MetricQuality.VALID
    )

    # --------------------------------------------------------
    # Variance
    # --------------------------------------------------------

    variance = create_metric(
        registry,
        "variance",
        2.5,
        confidence=0.90,
    )

    results["variance_created"] = (
        variance.quality
        == MetricQuality.VALID
    )

    # --------------------------------------------------------
    # Anomaly score
    # --------------------------------------------------------

    anomaly = create_metric(
        registry,
        "anomaly_score",
        0.72,
        confidence=0.81,
    )

    results["anomaly_is_c2"] = (
        anomaly.definition.claim_class
        == ClaimClass.C2
    )

    results["anomaly_requires_review"] = (
        anomaly.definition.human_review_required
        is True
    )

    # --------------------------------------------------------
    # Invalid confidence
    # --------------------------------------------------------

    bad_confidence = create_metric(
        registry,
        "confidence",
        1.5,
    )

    results["invalid_confidence_detected"] = (
        bad_confidence.quality
        == MetricQuality.INVALID
    )

    # --------------------------------------------------------
    # Non-finite value
    # --------------------------------------------------------

    nan_metric = create_metric(
        registry,
        "variance",
        float("nan"),
    )

    results["nan_detected"] = (
        nan_metric.quality
        == MetricQuality.NONFINITE
    )

    # --------------------------------------------------------
    # Metric set
    # --------------------------------------------------------

    metric_set = create_metric_set(
        "TEST_DATASET",
        [
            entropy,
            variance,
            anomaly,
        ],
        provenance={
            "source": "synthetic_test"
        },
    )

    valid, errors = metric_set.validate()

    results["metric_set_valid"] = valid

    results["metric_set_has_fingerprint"] = (
        len(
            metric_set.fingerprint()
        )
        == 64
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    summary = summarize_metric_set(
        metric_set
    )

    results["summary_created"] = (
        summary["metric_count"]
        == 3
    )

    # --------------------------------------------------------
    # Public payload validation
    # --------------------------------------------------------

    payload = {
        "name": "coupling",
        "value": -0.91,
        "confidence": 0.88,
    }

    payload_valid, payload_errors = (
        validate_metric_payload(
            payload,
            registry,
        )
    )

    results["payload_validation_passed"] = (
        payload_valid
    )

    # --------------------------------------------------------
    # Unknown/private metric rejection
    # --------------------------------------------------------

    private_payload = {
        "name": "internal_dsi_parameter",
        "value": 0.1,
    }

    private_valid, private_errors = (
        validate_metric_payload(
            private_payload,
            registry,
        )
    )

    results["private_metric_rejected"] = (
        private_valid is False
    )

    # --------------------------------------------------------
    # Security flags
    # --------------------------------------------------------

    contract = metrics_contract()

    results["proprietary_code_absent"] = (
        contract[
            "proprietary_algorithms_included"
        ] is False
    )

    results["raw_modification_disabled"] = (
        contract[
            "raw_data_modification_allowed"
        ] is False
    )

    results["medical_diagnosis_disabled"] = (
        contract[
            "medical_diagnosis_supported"
        ] is False
    )

    results["flight_certification_disabled"] = (
        contract[
            "flight_certification_supported"
        ] is False
    )

    # --------------------------------------------------------
    # Final
    # --------------------------------------------------------

    boolean_checks = [
        value
        for value in results.values()
        if isinstance(value, bool)
    ]

    results["all_metric_checks_passed"] = (
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
        "schema_version": (
            METRICS_SCHEMA_VERSION
        ),

        "role": (
            "Public analytics output validation "
            "and metric summarization layer."
        ),

        "proprietary_algorithm_included": False,
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
        "D³ VITAL-X — Module 18: metrics.py"
    )
    print("=" * 72)

    results = run_metrics_test()

    for key, value in results.items():
        print(f"{key}: {value}")

    print("=" * 72)

    if results[
        "all_metric_checks_passed"
    ]:
        print(
            "✅ METRICS MODULE TEST: PASS"
        )
    else:
        print(
            "❌ METRICS MODULE TEST: REVIEW REQUIRED"
        )

    print("=" * 72)
