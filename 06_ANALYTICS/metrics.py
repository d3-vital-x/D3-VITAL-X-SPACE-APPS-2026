# ============================================================
# D³ VITAL-X Space Intelligence Platform
# Module 18 — metrics.py
# Harmonized Version 1.1.1
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
#   ❌ proprietary physics coupling equations / models
#   ❌ MCMC / UTL / DVDH / DSI private algorithm source
#   ❌ clinical diagnosis
#   ❌ flight-control actuators
#   ❌ autonomous safety decisions
#
# It ONLY:
#   1. accepts public metric values
#   2. validates numerical values & limits
#   3. records provenance
#   4. assigns public quality states
#   5. summarizes metric collections
#   6. supports Modules 19–22
#   7. preserves claim-classification boundaries
#   8. preserves raw-data immutability
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
MODULE_VERSION = "1.1.1"
METRICS_SCHEMA_VERSION = "1.0"

PROPRIETARY_ALGORITHMS_INCLUDED = False
RAW_DATA_MODIFICATION_ALLOWED = False
MEDICAL_DIAGNOSIS_SUPPORTED = False
FLIGHT_CERTIFICATION_SUPPORTED = False
AUTONOMOUS_DECISION_SUPPORTED = False


# ============================================================
# ENUMS
# ============================================================

class MetricCategory(str, Enum):

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
    EXPLAINABILITY = "EXPLAINABILITY"

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

    VALID = "VALID"
    INVALID = "INVALID"
    MISSING = "MISSING"
    NONFINITE = "NONFINITE"
    LOW_QUALITY = "LOW_QUALITY"
    UNVERIFIED = "UNVERIFIED"


class ClaimClass(str, Enum):

    C1 = "C1"
    C2 = "C2"
    C3 = "C3"


# ============================================================
# SAFE UTILITIES
# ============================================================

def utc_timestamp() -> str:
    """
    Return timezone-aware UTC timestamp.
    """

    return datetime.now(timezone.utc).isoformat()


def generate_metric_id() -> str:
    """
    Generate unique public metric identifier.
    """

    return f"metric-{uuid.uuid4().hex}"


def canonical_json(payload: Any) -> str:
    """
    Deterministic JSON serialization.
    """

    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )


def calculate_sha256(payload: Any) -> str:
    """
    Calculate deterministic SHA-256 hash.
    """

    return hashlib.sha256(
        canonical_json(payload).encode("utf-8")
    ).hexdigest()


def is_finite_number(value: Any) -> bool:
    """
    Return True only for finite real numeric values.

    bool is intentionally rejected because:
        True == 1
        False == 0
    """

    if isinstance(value, bool):
        return False

    if not isinstance(value, (int, float)):
        return False

    return math.isfinite(float(value))


def safe_float(
    value: Any,
) -> Optional[float]:
    """
    Convert finite numeric value to float.
    """

    if not is_finite_number(value):
        return None

    return float(value)


def sanitize_identifier(
    value: Any,
    fallback: str = "unknown",
) -> str:
    """
    Sanitize public identifier.
    """

    if value is None:
        return fallback

    text = str(value).strip()

    if not text:
        return fallback

    return text[:128]


def is_numeric_uncertainty(
    value: Any,
) -> bool:
    """
    Check whether uncertainty is a simple finite scalar.
    """

    return is_finite_number(value)


def validate_uncertainty_value(
    value: Any,
) -> Tuple[bool, Optional[str]]:
    """
    Validate public uncertainty representation.

    Supported forms:

        1. None
        2. finite non-negative scalar
        3. dictionary representing structured uncertainty

    Structured uncertainty is intentionally passed to
    Module 21 for detailed validation.
    """

    if value is None:
        return True, None

    # Simple scalar uncertainty
    if isinstance(value, (int, float)):

        if not is_finite_number(value):
            return (
                False,
                "Uncertainty scalar must be finite.",
            )

        if float(value) < 0:
            return (
                False,
                "Uncertainty scalar cannot be negative.",
            )

        return True, None

    # Structured uncertainty
    if isinstance(value, dict):

        # Module 21 owns detailed uncertainty semantics.
        return True, None

    return (
        False,
        "Uncertainty must be a finite non-negative scalar "
        "or a structured dictionary.",
    )


# ============================================================
# METRIC DEFINITION
# ============================================================

@dataclass(frozen=True)
class MetricDefinition:

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

    def validate(
        self,
    ) -> Tuple[bool, List[str]]:

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

    metric_id: str

    definition: MetricDefinition

    value: Any = None

    quality: MetricQuality = (
        MetricQuality.UNVERIFIED
    )

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

    def validate(
        self,
    ) -> Tuple[bool, List[str]]:

        errors: List[str] = []

        # ----------------------------------------------------
        # Definition
        # ----------------------------------------------------

        definition_valid, definition_errors = (
            self.definition.validate()
        )

        if not definition_valid:
            errors.extend(
                definition_errors
            )

        # ----------------------------------------------------
        # Metric ID
        # ----------------------------------------------------

        if not self.metric_id:

            errors.append(
                "metric_id is required."
            )

        # ----------------------------------------------------
        # Null handling
        # ----------------------------------------------------

        if self.value is None:

            if not self.definition.nullable:

                errors.append(
                    f"Metric '{self.definition.name}' "
                    "does not allow null values."
                )

            # Still validate confidence/uncertainty.
            uncertainty_valid, uncertainty_error = (
                validate_uncertainty_value(
                    self.uncertainty
                )
            )

            if not uncertainty_valid:
                errors.append(
                    uncertainty_error
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

            # Confidence metric itself must be [0,1].
            if (
                self.definition.name.lower()
                == "confidence"
            ):

                if is_finite_number(
                    self.value
                ):

                    if not (
                        0.0
                        <= float(self.value)
                        <= 1.0
                    ):

                        errors.append(
                            "Confidence metric value "
                            "must be between 0 and 1."
                        )

        # ----------------------------------------------------
        # Confidence metadata
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

        # ----------------------------------------------------
        # Uncertainty boundary
        # ----------------------------------------------------

        uncertainty_valid, uncertainty_error = (
            validate_uncertainty_value(
                self.uncertainty
            )
        )

        if not uncertainty_valid:

            errors.append(
                uncertainty_error
            )

        return (
            len(errors) == 0,
            errors,
        )

    def evaluate_quality(
        self,
    ) -> MetricQuality:

        # ----------------------------------------------------
        # Missing
        # ----------------------------------------------------

        if self.value is None:

            self.quality = (
                MetricQuality.MISSING
            )

            return self.quality

        # ----------------------------------------------------
        # Scalar quality
        # ----------------------------------------------------

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

            # Confidence metric boundary
            if (
                self.definition.name.lower()
                == "confidence"
            ):

                if not (
                    0.0
                    <= float(self.value)
                    <= 1.0
                ):

                    self.quality = (
                        MetricQuality.INVALID
                    )

                    return self.quality

        # ----------------------------------------------------
        # Confidence metadata
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Uncertainty boundary
        # ----------------------------------------------------

        uncertainty_valid, _ = (
            validate_uncertainty_value(
                self.uncertainty
            )
        )

        if not uncertainty_valid:

            self.quality = (
                MetricQuality.INVALID
            )

            return self.quality

        # ----------------------------------------------------
        # Passed public validation
        # ----------------------------------------------------

        self.quality = (
            MetricQuality.VALID
        )

        return self.quality

    def fingerprint(self) -> str:

        payload = {

            "metric_id": self.metric_id,

            "name": (
                self.definition.name
            ),

            "category": (
                self.definition.category.value
            ),

            "value_type": (
                self.definition.value_type.value
            ),

            "value": self.value,

            "quality": (
                self.quality.value
            ),

            "confidence": self.confidence,

            "uncertainty": self.uncertainty,

            "source_dataset_id": (
                self.source_dataset_id
            ),

            "source_hash": (
                self.source_hash
            ),
        }

        return calculate_sha256(
            payload
        )

    def to_dict(
        self,
    ) -> Dict[str, Any]:

        result = asdict(self)

        result["definition"][
            "category"
        ] = self.definition.category.value

        result["definition"][
            "value_type"
        ] = self.definition.value_type.value

        result["definition"][
            "claim_class"
        ] = self.definition.claim_class.value

        result["quality"] = (
            self.quality.value
        )

        result["fingerprint"] = (
            self.fingerprint()
        )

        return result


# ============================================================
# METRIC SET
# ============================================================

@dataclass
class MetricSet:

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

    def validate(
        self,
    ) -> Tuple[bool, List[str]]:

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

            name = (
                metric.definition.name
            )

            if name in seen_names:

                errors.append(
                    f"Duplicate metric name: {name}"
                )

            seen_names.add(name)

        return (
            len(errors) == 0,
            errors,
        )

    def evaluate_quality(
        self,
    ) -> None:

        for metric in self.metrics:

            metric.evaluate_quality()

    def get(
        self,
        name: str,
    ) -> Optional[MetricValue]:

        name = (
            str(name)
            .strip()
            .lower()
        )

        for metric in self.metrics:

            if (
                metric.definition.name.lower()
                == name
            ):

                return metric

        return None

    def names(
        self,
    ) -> List[str]:

        return [
            metric.definition.name
            for metric in self.metrics
        ]

    def quality_summary(
        self,
    ) -> Dict[str, int]:

        summary = {
            quality.value: 0
            for quality in MetricQuality
        }

        for metric in self.metrics:

            summary[
                metric.quality.value
            ] += 1

        return summary

    def claim_class_summary(
        self,
    ) -> Dict[str, int]:

        summary = {
            claim.value: 0
            for claim in ClaimClass
        }

        for metric in self.metrics:

            summary[
                metric.definition.claim_class.value
            ] += 1

        return summary

    def fingerprint(
        self,
    ) -> str:

        payload = {

            "set_id": self.set_id,

            "dataset_id": self.dataset_id,

            "schema_version": (
                self.schema_version
            ),

            "metrics": [
                metric.fingerprint()
                for metric in self.metrics
            ],
        }

        return calculate_sha256(
            payload
        )

    def to_dict(
        self,
    ) -> Dict[str, Any]:

        return {

            "set_id": self.set_id,

            "dataset_id": self.dataset_id,

            "schema_version": (
                self.schema_version
            ),

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

            "fingerprint": (
                self.fingerprint()
            ),
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
# METRIC REGISTRY
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

        key = (
            definition.name.lower()
        )

        if key in self._definitions:

            raise ValueError(
                f"Metric already registered: "
                f"{definition.name}"
            )

        self._definitions[
            key
        ] = definition

    def get(
        self,
        name: str,
    ) -> Optional[MetricDefinition]:

        return self._definitions.get(
            str(name)
            .strip()
            .lower()
        )

    def names(
        self,
    ) -> List[str]:

        return sorted(
            self._definitions.keys()
        )

    def definitions(
        self,
    ) -> List[MetricDefinition]:

        return list(
            self._definitions.values()
        )


# ============================================================
# STANDARD PUBLIC METRIC REGISTRY
# Harmonized with Modules 19–22
# ============================================================

def create_standard_metric_registry(
) -> MetricRegistry:

    registry = MetricRegistry()

    # --------------------------------------------------------
    # Core public metrics
    # --------------------------------------------------------

    registry.register(
        MetricDefinition(
            name="entropy",
            category=MetricCategory.ENTROPY,
            value_type=MetricValueType.SCALAR,
            description=(
                "Public entropy metric."
            ),
        )
    )

    registry.register(
        MetricDefinition(
            name="variance",
            category=MetricCategory.VARIANCE,
            value_type=MetricValueType.SCALAR,
            description=(
                "Public variance metric."
            ),
        )
    )

    registry.register(
        MetricDefinition(
            name="gradient",
            category=MetricCategory.GRADIENT,
            value_type=MetricValueType.SCALAR,
            description=(
                "Public gradient metric."
            ),
        )
    )

    registry.register(
        MetricDefinition(
            name="coupling",
            category=MetricCategory.COUPLING,
            value_type=MetricValueType.SCALAR,
            description=(
                "Public coupling metric."
            ),
        )
    )

    # --------------------------------------------------------
    # Quality
    # --------------------------------------------------------

    registry.register(
        MetricDefinition(
            name="signal_quality",
            category=MetricCategory.QUALITY,
            value_type=MetricValueType.SCALAR,
            description=(
                "Normalized public signal-quality indicator."
            ),
        )
    )

    registry.register(
        MetricDefinition(
            name="confidence",
            category=MetricCategory.QUALITY,
            value_type=MetricValueType.SCALAR,
            description=(
                "Normalized computational confidence indicator."
            ),
        )
    )

    # --------------------------------------------------------
    # Uncertainty
    # --------------------------------------------------------

    registry.register(
        MetricDefinition(
            name="uncertainty",
            category=MetricCategory.UNCERTAINTY,
            value_type=MetricValueType.SCALAR,
            description=(
                "Public uncertainty magnitude."
            ),
        )
    )

    # --------------------------------------------------------
    # Module 19 — Transition Analysis
    # --------------------------------------------------------

    registry.register(
        MetricDefinition(
            name="transition_index",
            category=MetricCategory.TRANSITION,
            value_type=MetricValueType.SCALAR,
            human_review_required=True,
            description=(
                "Public transition indicator."
            ),
        )
    )

    registry.register(
        MetricDefinition(
            name="transition_score",
            category=MetricCategory.TRANSITION,
            value_type=MetricValueType.SCALAR,
            human_review_required=True,
            description=(
                "Public transition-review score."
            ),
        )
    )

    # --------------------------------------------------------
    # Module 20 — Anomaly Scoring
    # --------------------------------------------------------

    registry.register(
        MetricDefinition(
            name="anomaly_score",
            category=MetricCategory.ANOMALY,
            value_type=MetricValueType.SCALAR,
            human_review_required=True,
            description=(
                "Research anomaly-prioritization indicator."
            ),
        )
    )

    registry.register(
        MetricDefinition(
            name="anomaly_rank",
            category=MetricCategory.ANOMALY,
            value_type=MetricValueType.SCALAR,
            human_review_required=True,
            description=(
                "Research ordering/index for anomaly review."
            ),
        )
    )

    # --------------------------------------------------------
    # Module 21 — Uncertainty
    # --------------------------------------------------------

    registry.register(
        MetricDefinition(
            name="uncertainty_lower",
            category=MetricCategory.UNCERTAINTY,
            value_type=MetricValueType.SCALAR,
            description=(
                "Lower reported uncertainty bound."
            ),
        )
    )

    registry.register(
        MetricDefinition(
            name="uncertainty_upper",
            category=MetricCategory.UNCERTAINTY,
            value_type=MetricValueType.SCALAR,
            description=(
                "Upper reported uncertainty bound."
            ),
        )
    )

    registry.register(
        MetricDefinition(
            name="coverage_probability",
            category=MetricCategory.UNCERTAINTY,
            value_type=MetricValueType.SCALAR,
            description=(
                "User-supplied statistical coverage quantity."
            ),
        )
    )

    # --------------------------------------------------------
    # Module 22 — Explainability
    # --------------------------------------------------------

    registry.register(
        MetricDefinition(
            name="evidence_count",
            category=MetricCategory.EXPLAINABILITY,
            value_type=MetricValueType.SCALAR,
            description=(
                "Number of public evidence items."
            ),
        )
    )

    registry.register(
        MetricDefinition(
            name="supporting_evidence_count",
            category=MetricCategory.EXPLAINABILITY,
            value_type=MetricValueType.SCALAR,
            description=(
                "Number of supporting evidence items."
            ),
        )
    )

    registry.register(
        MetricDefinition(
            name="contradicting_evidence_count",
            category=MetricCategory.EXPLAINABILITY,
            value_type=MetricValueType.SCALAR,
            description=(
                "Number of contradicting evidence items."
            ),
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
    provenance: Optional[
        Dict[str, Any]
    ] = None,
    metadata: Optional[
        Dict[str, Any]
    ] = None,
) -> MetricValue:

    definition = registry.get(
        name
    )

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
    metrics: Optional[
        List[MetricValue]
    ] = None,
    *,
    provenance: Optional[
        Dict[str, Any]
    ] = None,
    metadata: Optional[
        Dict[str, Any]
    ] = None,
) -> MetricSet:

    metric_set = MetricSet(

        set_id=(
            f"metric-set-"
            f"{uuid.uuid4().hex}"
        ),

        dataset_id=(
            sanitize_identifier(
                dataset_id
            )
        ),

        metrics=(
            metrics or []
        ),

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
# SAFE SUMMARY
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
            and is_finite_number(
                metric.value
            )
        ):

            numeric_values[
                metric.definition.name
            ] = float(
                metric.value
            )

    return {

        "dataset_id":
            metric_set.dataset_id,

        "metric_count":
            len(metric_set.metrics),

        "numeric_metric_count":
            len(numeric_values),

        "metric_names":
            metric_set.names(),

        "quality_summary":
            metric_set.quality_summary(),

        "claim_class_summary":
            metric_set.claim_class_summary(),

        "numeric_values":
            numeric_values,

        "fingerprint":
            metric_set.fingerprint(),
    }


# ============================================================
# PAYLOAD VALIDATION
# ============================================================

def validate_metric_payload(
    payload: Dict[str, Any],
    registry: Optional[
        MetricRegistry
    ] = None,
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
            [
                "Metric payload must be a dictionary."
            ],
        )

    name = payload.get(
        "name"
    )

    if not name:

        errors.append(
            "Metric payload requires 'name'."
        )

        return (
            False,
            errors,
        )

    definition = registry.get(
        name
    )

    if definition is None:

        errors.append(
            f"Unknown metric: {name}"
        )

        return (
            False,
            errors,
        )

    value = payload.get(
        "value"
    )

    # --------------------------------------------------------
    # Scalar
    # --------------------------------------------------------

    if (
        definition.value_type
        == MetricValueType.SCALAR
    ):

        if (
            value is not None
            and not is_finite_number(
                value
            )
        ):

            errors.append(
                f"Metric '{name}' "
                "requires a finite scalar."
            )

        if (
            definition.name.lower()
            == "confidence"
            and value is not None
        ):

            if not (
                0.0
                <= float(value)
                <= 1.0
            ):

                errors.append(
                    "Confidence metric value "
                    "must be between 0 and 1."
                )

    # --------------------------------------------------------
    # Confidence metadata
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Uncertainty
    # --------------------------------------------------------

    uncertainty = payload.get(
        "uncertainty"
    )

    uncertainty_valid, uncertainty_error = (
        validate_uncertainty_value(
            uncertainty
        )
    )

    if not uncertainty_valid:

        errors.append(
            uncertainty_error
        )

    return (
        len(errors) == 0,
        errors,
    )


# ============================================================
# METRICS CONTRACT
# ============================================================

def metrics_contract() -> Dict[str, Any]:

    registry = (
        create_standard_metric_registry()
    )

    return {

        "module":
            MODULE_NAME,

        "version":
            MODULE_VERSION,

        "schema_version":
            METRICS_SCHEMA_VERSION,

        "purpose": (
            "Public analytics result validation, "
            "quality assessment, provenance, "
            "and metric summarization."
        ),

        "proprietary_algorithms_included":
            PROPRIETARY_ALGORITHMS_INCLUDED,

        "raw_data_modification_allowed":
            RAW_DATA_MODIFICATION_ALLOWED,

        "medical_diagnosis_supported":
            MEDICAL_DIAGNOSIS_SUPPORTED,

        "flight_certification_supported":
            FLIGHT_CERTIFICATION_SUPPORTED,

        "autonomous_decision_supported":
            AUTONOMOUS_DECISION_SUPPORTED,

        "registered_metrics":
            registry.names(),

        "calculation_policy": (
            "Metric values are accepted as public "
            "results; proprietary generation algorithms "
            "are not implemented in this module."
        ),

        "uncertainty_policy": (
            "Simple finite non-negative uncertainty "
            "values are validated here; structured "
            "uncertainty semantics belong to Module 21."
        ),

        "review_policy": (
            "Metrics marked human_review_required=True "
            "must not be interpreted as autonomous decisions."
        ),
    }


# ============================================================
# SECURITY / ARCHITECTURE SELF-TEST
# ============================================================

def run_metrics_test() -> Dict[str, Any]:

    results: Dict[str, Any] = {}

    registry = (
        create_standard_metric_registry()
    )

    # --------------------------------------------------------
    # Registry
    # --------------------------------------------------------

    results[
        "registry_created"
    ] = isinstance(
        registry,
        MetricRegistry,
    )

    results[
        "standard_metric_count_expanded"
    ] = (
        len(registry.names()) >= 17
    )

    # --------------------------------------------------------
    # Core metrics
    # --------------------------------------------------------

    entropy = create_metric(
        registry,
        "entropy",
        1.234,
        confidence=0.95,
        source_dataset_id=(
            "TEST_DATASET"
        ),
        source_hash=(
            "a" * 64
        ),
    )

    results[
        "entropy_created"
    ] = (
        entropy.quality
        == MetricQuality.VALID
    )

    variance = create_metric(
        registry,
        "variance",
        2.5,
        confidence=0.90,
    )

    results[
        "variance_created"
    ] = (
        variance.quality
        == MetricQuality.VALID
    )

    # --------------------------------------------------------
    # Anomaly
    # --------------------------------------------------------

    anomaly = create_metric(
        registry,
        "anomaly_score",
        0.72,
        confidence=0.81,
    )

    results[
        "anomaly_is_c2"
    ] = (
        anomaly.definition.claim_class
        == ClaimClass.C2
    )

    results[
        "anomaly_requires_review"
    ] = (
        anomaly.definition
        .human_review_required
        is True
    )

    # --------------------------------------------------------
    # Modules 19–22
    # --------------------------------------------------------

    transition = create_metric(
        registry,
        "transition_score",
        0.88,
    )

    uncertainty_low = create_metric(
        registry,
        "uncertainty_lower",
        0.12,
    )

    evidence_count = create_metric(
        registry,
        "evidence_count",
        3,
    )

    results[
        "module_19_22_metrics_registered"
    ] = (
        transition.quality
        == MetricQuality.VALID
        and uncertainty_low.quality
        == MetricQuality.VALID
        and evidence_count.quality
        == MetricQuality.VALID
    )

    # --------------------------------------------------------
    # Invalid confidence
    # --------------------------------------------------------

    bad_confidence = create_metric(
        registry,
        "confidence",
        1.5,
    )

    results[
        "invalid_confidence_detected"
    ] = (
        bad_confidence.quality
        == MetricQuality.INVALID
    )

    # --------------------------------------------------------
    # NaN
    # --------------------------------------------------------

    nan_metric = create_metric(
        registry,
        "variance",
        float("nan"),
    )

    results[
        "nan_detected"
    ] = (
        nan_metric.quality
        == MetricQuality.NONFINITE
    )

    # --------------------------------------------------------
    # Negative uncertainty
    # --------------------------------------------------------

    negative_uncertainty = create_metric(
        registry,
        "variance",
        2.0,
        uncertainty=-0.5,
    )

    results[
        "negative_uncertainty_detected"
    ] = (
        negative_uncertainty.quality
        == MetricQuality.INVALID
    )

    # --------------------------------------------------------
    # NaN uncertainty
    # --------------------------------------------------------

    nan_uncertainty = create_metric(
        registry,
        "variance",
        2.0,
        uncertainty=float("nan"),
    )

    results[
        "nan_uncertainty_detected"
    ] = (
        nan_uncertainty.quality
        == MetricQuality.INVALID
    )

    # --------------------------------------------------------
    # Structured uncertainty accepted
    # --------------------------------------------------------

    structured_uncertainty = create_metric(
        registry,
        "variance",
        2.0,
        uncertainty={
            "uncertainty": 0.2,
            "type": "standard_deviation",
            "source": "computational",
        },
    )

    results[
        "structured_uncertainty_accepted"
    ] = (
        structured_uncertainty.quality
        == MetricQuality.VALID
    )

    # --------------------------------------------------------
    # Metric Set
    # --------------------------------------------------------

    metric_set = create_metric_set(
        "TEST_DATASET",
        [
            entropy,
            variance,
            anomaly,
            transition,
            uncertainty_low,
            evidence_count,
        ],
        provenance={
            "source": "synthetic_test"
        },
    )

    valid, errors = (
        metric_set.validate()
    )

    results[
        "metric_set_valid"
    ] = valid

    results[
        "metric_set_has_fingerprint"
    ] = (
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

    results[
        "summary_created"
    ] = (
        summary[
            "metric_count"
        ]
        == 6
    )

    # --------------------------------------------------------
    # Public payload
    # --------------------------------------------------------

    payload = {

        "name":
            "coupling",

        "value":
            -0.91,

        "confidence":
            0.88,

        "uncertainty":
            0.05,
    }

    payload_valid, _ = (
        validate_metric_payload(
            payload,
            registry,
        )
    )

    results[
        "payload_validation_passed"
    ] = payload_valid

    # --------------------------------------------------------
    # Private metric rejection
    # --------------------------------------------------------

    private_payload = {

        "name":
            "internal_dsi_parameter",

        "value":
            0.1,
    }

    private_valid, _ = (
        validate_metric_payload(
            private_payload,
            registry,
        )
    )

    results[
        "private_metric_rejected"
    ] = (
        private_valid is False
    )

    # --------------------------------------------------------
    # Contract
    # --------------------------------------------------------

    contract = (
        metrics_contract()
    )

    results[
        "proprietary_code_absent"
    ] = (
        contract[
            "proprietary_algorithms_included"
        ]
        is False
    )

    results[
        "raw_modification_disabled"
    ] = (
        contract[
            "raw_data_modification_allowed"
        ]
        is False
    )

    results[
        "medical_diagnosis_disabled"
    ] = (
        contract[
            "medical_diagnosis_supported"
        ]
        is False
    )

    results[
        "flight_certification_disabled"
    ] = (
        contract[
            "flight_certification_supported"
        ]
        is False
    )

    results[
        "autonomous_decision_disabled"
    ] = (
        contract[
            "autonomous_decision_supported"
        ]
        is False
    )

    # --------------------------------------------------------
    # Final status
    # --------------------------------------------------------

    boolean_checks = [
        value
        for value in results.values()
        if isinstance(value, bool)
    ]

    results[
        "all_metric_checks_passed"
    ] = (
        all(boolean_checks)
        if boolean_checks
        else False
    )

    return results


# ============================================================
# MODULE INFORMATION
# ============================================================

def module_info() -> Dict[str, Any]:

    return {

        "module_name":
            MODULE_NAME,

        "module_version":
            MODULE_VERSION,

        "schema_version":
            METRICS_SCHEMA_VERSION,

        "role": (
            "Public analytics output validation, "
            "quality, provenance, and summarization layer."
        ),

        "proprietary_algorithm_included":
            False,

        "raw_data_modification":
            False,

        "medical_diagnosis":
            False,

        "flight_certification":
            False,

        "autonomous_decision":
            False,

        "harmonized_modules": [
            "19_transition_analysis.py",
            "20_anomaly_scoring.py",
            "21_uncertainty.py",
            "22_explainability.py",
        ],
    }


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    print("=" * 72)

    print(
        "D³ VITAL-X Space Intelligence Platform"
    )

    print(
        "Module 18 — metrics.py"
    )

    print(
        f"Version: {MODULE_VERSION}"
    )

    print("=" * 72)

    results = run_metrics_test()

    for key, value in results.items():

        status = (
            "✅"
            if value
            else "❌"
        )

        print(
            f"{status} {key}: {value}"
        )

    print("=" * 72)

    if results[
        "all_metric_checks_passed"
    ]:

        print(
            "🚀 METRICS MODULE TEST: PASS"
        )

    else:

        print(
            "❌ METRICS MODULE TEST: REVIEW REQUIRED"
        )

    print("=" * 72)
