# ============================================================
# 21. uncertainty.py
# D³ VITAL-X Space Intelligence Platform
# Public Uncertainty & Confidence Layer
#
# Purpose:
#   - Represent measurement / computational uncertainty
#   - Calculate generic uncertainty intervals
#   - Propagate independent uncertainties
#   - Provide confidence metadata
#   - Support reproducibility and reviewer-safe reporting
#
# IMPORTANT:
#   - No proprietary D³/UTL algorithm
#   - No v10/v11 source
#   - No medical diagnosis
#   - No spacecraft flight certification
#   - No raw-data modification
#   - No physical-causality claim
# ============================================================

from __future__ import annotations

import json
import math
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple


# ============================================================
# MODULE METADATA
# ============================================================

MODULE_NAME = "uncertainty"
MODULE_VERSION = "1.0.0"
UNCERTAINTY_SCHEMA_VERSION = "1.0"

PROPRIETARY_ALGORITHMS_INCLUDED = False
RAW_DATA_MODIFICATION_ALLOWED = False
MEDICAL_DIAGNOSIS_SUPPORTED = False
FLIGHT_CERTIFICATION_SUPPORTED = False


# ============================================================
# ENUMS
# ============================================================

class UncertaintyType(str, Enum):
    """
    Generic uncertainty categories.
    """

    ABSOLUTE = "absolute"
    RELATIVE = "relative"
    STANDARD_DEVIATION = "standard_deviation"
    CONFIDENCE_INTERVAL = "confidence_interval"
    RANGE = "range"
    UNKNOWN = "unknown"


class UncertaintySource(str, Enum):
    """
    Describes where the uncertainty information originated.
    """

    MEASUREMENT = "measurement"
    COMPUTATIONAL = "computational"
    PROPAGATED = "propagated"
    EMPIRICAL = "empirical"
    USER_SUPPLIED = "user_supplied"
    UNKNOWN = "unknown"


class ConfidenceLevel(str, Enum):
    """
    Qualitative reporting category.

    These are reporting labels only.
    They are NOT scientific significance levels.
    """

    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"
    UNKNOWN = "unknown"


class ClaimClass(str, Enum):
    """
    Public claim classification.
    """

    C1 = "C1"   # Directly measured / directly reported
    C2 = "C2"   # Computationally derived
    C3 = "C3"   # Hypothesis / future interpretation


# ============================================================
# BASIC UTILITIES
# ============================================================

def utc_timestamp() -> str:
    """
    Return timezone-aware UTC timestamp.
    """
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value: Any) -> str:
    """
    Deterministic JSON serialization.
    """
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )


def calculate_sha256(value: Any) -> str:
    """
    Calculate deterministic SHA-256 hash.
    """
    payload = canonical_json(value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def is_finite_number(value: Any) -> bool:
    """
    Check whether a value is a finite real number.
    """
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def safe_float(value: Any) -> Optional[float]:
    """
    Convert to float if finite.
    """
    if not is_finite_number(value):
        return None

    return float(value)


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    """
    Clamp a numeric value to [lower, upper].
    """
    return max(lower, min(upper, float(value)))


# ============================================================
# UNCERTAINTY OBJECT
# ============================================================

@dataclass
class UncertaintyValue:
    """
    Public representation of uncertainty associated with a value.

    The object stores uncertainty metadata only.
    It does not infer physical meaning.
    """

    value: float

    uncertainty: Optional[float] = None

    uncertainty_type: UncertaintyType = UncertaintyType.UNKNOWN

    source: UncertaintySource = UncertaintySource.UNKNOWN

    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None

    confidence_level: ConfidenceLevel = ConfidenceLevel.UNKNOWN

    confidence: Optional[float] = None

    unit: Optional[str] = None

    claim_class: ClaimClass = ClaimClass.C2

    description: str = ""

    provenance: Dict[str, Any] = field(default_factory=dict)

    created_at: str = field(default_factory=utc_timestamp)

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate uncertainty representation.
        """

        errors: List[str] = []

        if not is_finite_number(self.value):
            errors.append("value must be finite.")

        if self.uncertainty is not None:

            if not is_finite_number(self.uncertainty):
                errors.append("uncertainty must be finite.")

            elif float(self.uncertainty) < 0:
                errors.append("uncertainty cannot be negative.")

        if self.lower_bound is not None:

            if not is_finite_number(self.lower_bound):
                errors.append("lower_bound must be finite.")

        if self.upper_bound is not None:

            if not is_finite_number(self.upper_bound):
                errors.append("upper_bound must be finite.")

        if (
            self.lower_bound is not None
            and self.upper_bound is not None
            and float(self.lower_bound) > float(self.upper_bound)
        ):
            errors.append(
                "lower_bound cannot be greater than upper_bound."
            )

        if self.confidence is not None:

            if not is_finite_number(self.confidence):
                errors.append("confidence must be finite.")

            elif not 0.0 <= float(self.confidence) <= 1.0:
                errors.append(
                    "confidence must be between 0 and 1."
                )

        return len(errors) == 0, errors

    def interval(self) -> Optional[Tuple[float, float]]:
        """
        Return uncertainty interval if available.
        """

        if (
            self.lower_bound is not None
            and self.upper_bound is not None
        ):
            return (
                float(self.lower_bound),
                float(self.upper_bound),
            )

        if self.uncertainty is not None:

            u = abs(float(self.uncertainty))
            v = float(self.value)

            return (
                v - u,
                v + u,
            )

        return None

    def relative_uncertainty(self) -> Optional[float]:
        """
        Return |uncertainty / value|.

        Returns None when the central value is zero or
        uncertainty is unavailable.
        """

        if self.uncertainty is None:
            return None

        value = float(self.value)

        if value == 0.0:
            return None

        return abs(float(self.uncertainty) / value)

    def fingerprint(self) -> str:
        """
        Stable fingerprint of this uncertainty object.
        """

        return calculate_sha256(
            {
                "value": self.value,
                "uncertainty": self.uncertainty,
                "uncertainty_type": self.uncertainty_type.value,
                "source": self.source.value,
                "lower_bound": self.lower_bound,
                "upper_bound": self.upper_bound,
                "confidence_level": self.confidence_level.value,
                "confidence": self.confidence,
                "unit": self.unit,
                "claim_class": self.claim_class.value,
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize object to dictionary.
        """

        payload = asdict(self)

        payload["uncertainty_type"] = self.uncertainty_type.value
        payload["source"] = self.source.value
        payload["confidence_level"] = self.confidence_level.value
        payload["claim_class"] = self.claim_class.value

        payload["relative_uncertainty"] = self.relative_uncertainty()
        payload["interval"] = self.interval()
        payload["fingerprint"] = self.fingerprint()

        return payload


# ============================================================
# CONFIDENCE UTILITIES
# ============================================================

def confidence_level_from_score(
    confidence: Optional[float],
) -> ConfidenceLevel:
    """
    Convert normalized confidence score into a reporting label.

    IMPORTANT:
    These thresholds are presentation conventions,
    not statistical significance thresholds.
    """

    if confidence is None:
        return ConfidenceLevel.UNKNOWN

    if not is_finite_number(confidence):
        return ConfidenceLevel.UNKNOWN

    c = clamp(float(confidence))

    if c < 0.20:
        return ConfidenceLevel.VERY_LOW

    if c < 0.40:
        return ConfidenceLevel.LOW

    if c < 0.60:
        return ConfidenceLevel.MODERATE

    if c < 0.80:
        return ConfidenceLevel.HIGH

    return ConfidenceLevel.VERY_HIGH


def confidence_from_relative_uncertainty(
    relative_uncertainty: Optional[float],
    scale: float = 1.0,
) -> Optional[float]:
    """
    Convert relative uncertainty into a bounded confidence indicator.

    This is a generic reporting transformation.
    It is NOT a probability of correctness.
    """

    if relative_uncertainty is None:
        return None

    if not is_finite_number(relative_uncertainty):
        return None

    if not is_finite_number(scale) or float(scale) <= 0:
        raise ValueError("scale must be a positive finite number.")

    ru = max(0.0, float(relative_uncertainty))
    s = float(scale)

    confidence = 1.0 / (1.0 + ru / s)

    return clamp(confidence)


# ============================================================
# CONSTRUCTORS
# ============================================================

def create_uncertainty(
    value: float,
    uncertainty: Optional[float] = None,
    uncertainty_type: UncertaintyType = UncertaintyType.UNKNOWN,
    source: UncertaintySource = UncertaintySource.UNKNOWN,
    lower_bound: Optional[float] = None,
    upper_bound: Optional[float] = None,
    confidence: Optional[float] = None,
    unit: Optional[str] = None,
    claim_class: ClaimClass = ClaimClass.C2,
    description: str = "",
    provenance: Optional[Dict[str, Any]] = None,
) -> UncertaintyValue:
    """
    Create and validate an UncertaintyValue.
    """

    obj = UncertaintyValue(
        value=float(value),
        uncertainty=(
            None
            if uncertainty is None
            else float(uncertainty)
        ),
        uncertainty_type=uncertainty_type,
        source=source,
        lower_bound=(
            None
            if lower_bound is None
            else float(lower_bound)
        ),
        upper_bound=(
            None
            if upper_bound is None
            else float(upper_bound)
        ),
        confidence=(
            None
            if confidence is None
            else float(confidence)
        ),
        confidence_level=confidence_level_from_score(
            confidence
        ),
        unit=unit,
        claim_class=claim_class,
        description=description,
        provenance=provenance or {},
    )

    valid, errors = obj.validate()

    if not valid:
        raise ValueError(
            "Invalid uncertainty object: "
            + "; ".join(errors)
        )

    return obj


# ============================================================
# GENERIC INTERVAL HELPERS
# ============================================================

def symmetric_interval(
    value: float,
    uncertainty: float,
) -> Tuple[float, float]:
    """
    Construct a symmetric interval:

        [value - uncertainty, value + uncertainty]
    """

    if not is_finite_number(value):
        raise ValueError("value must be finite.")

    if not is_finite_number(uncertainty):
        raise ValueError("uncertainty must be finite.")

    u = float(uncertainty)

    if u < 0:
        raise ValueError("uncertainty cannot be negative.")

    v = float(value)

    return v - u, v + u


def relative_interval(
    value: float,
    relative_uncertainty: float,
) -> Tuple[float, float]:
    """
    Construct interval from relative uncertainty.

    Example:
        value = 100
        relative_uncertainty = 0.10

        -> [90, 110]
    """

    if not is_finite_number(value):
        raise ValueError("value must be finite.")

    if not is_finite_number(relative_uncertainty):
        raise ValueError(
            "relative_uncertainty must be finite."
        )

    r = float(relative_uncertainty)

    if r < 0:
        raise ValueError(
            "relative_uncertainty cannot be negative."
        )

    v = float(value)

    delta = abs(v) * r

    return v - delta, v + delta


# ============================================================
# UNCERTAINTY PROPAGATION
# ============================================================

def propagate_independent_uncertainties(
    values: Sequence[float],
    uncertainties: Sequence[float],
) -> float:
    """
    Generic root-sum-square propagation for independent
    additive uncertainty components:

        u_total = sqrt(sum(u_i^2))

    This function does not infer correlations or physical
    relationships between quantities.
    """

    if len(values) != len(uncertainties):
        raise ValueError(
            "values and uncertainties must have equal length."
        )

    if len(uncertainties) == 0:
        raise ValueError(
            "At least one uncertainty is required."
        )

    clean_uncertainties: List[float] = []

    for uncertainty in uncertainties:

        if not is_finite_number(uncertainty):
            raise ValueError(
                "All uncertainties must be finite."
            )

        u = float(uncertainty)

        if u < 0:
            raise ValueError(
                "Uncertainties cannot be negative."
            )

        clean_uncertainties.append(u)

    return math.sqrt(
        sum(u * u for u in clean_uncertainties)
    )


def propagate_weighted_uncertainties(
    uncertainties: Sequence[float],
    weights: Sequence[float],
) -> float:
    """
    Generic weighted root-sum-square propagation.

        u = sqrt(sum((w_i * u_i)^2))

    This assumes the supplied weights already represent
    the intended computational combination.
    """

    if len(uncertainties) != len(weights):
        raise ValueError(
            "uncertainties and weights must have equal length."
        )

    if len(uncertainties) == 0:
        raise ValueError(
            "At least one uncertainty is required."
        )

    total = 0.0

    for uncertainty, weight in zip(
        uncertainties,
        weights,
    ):

        if not is_finite_number(uncertainty):
            raise ValueError(
                "All uncertainties must be finite."
            )

        if not is_finite_number(weight):
            raise ValueError(
                "All weights must be finite."
            )

        u = float(uncertainty)
        w = float(weight)

        if u < 0:
            raise ValueError(
                "Uncertainty cannot be negative."
            )

        total += (w * u) ** 2

    return math.sqrt(total)


# ============================================================
# BATCH UNCERTAINTY SUMMARY
# ============================================================

@dataclass
class UncertaintySummary:
    """
    Summary of uncertainty across multiple public metrics.
    """

    count: int

    mean_absolute_uncertainty: Optional[float]

    median_absolute_uncertainty: Optional[float]

    max_absolute_uncertainty: Optional[float]

    mean_relative_uncertainty: Optional[float]

    coverage: float

    confidence: Optional[float]

    confidence_level: ConfidenceLevel

    claim_class: ClaimClass = ClaimClass.C2

    created_at: str = field(default_factory=utc_timestamp)

    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:

        payload = asdict(self)

        payload["confidence_level"] = (
            self.confidence_level.value
        )

        payload["claim_class"] = (
            self.claim_class.value
        )

        return payload


def _median(values: Sequence[float]) -> float:
    """
    Minimal dependency-free median.
    """

    if not values:
        raise ValueError(
            "Cannot calculate median of empty sequence."
        )

    ordered = sorted(float(v) for v in values)

    n = len(ordered)

    mid = n // 2

    if n % 2 == 0:
        return (
            ordered[mid - 1] + ordered[mid]
        ) / 2.0

    return ordered[mid]


def summarize_uncertainties(
    uncertainty_values: Sequence[UncertaintyValue],
) -> UncertaintySummary:
    """
    Summarize a collection of uncertainty objects.
    """

    if len(uncertainty_values) == 0:

        return UncertaintySummary(
            count=0,
            mean_absolute_uncertainty=None,
            median_absolute_uncertainty=None,
            max_absolute_uncertainty=None,
            mean_relative_uncertainty=None,
            coverage=0.0,
            confidence=None,
            confidence_level=ConfidenceLevel.UNKNOWN,
        )

    absolute_values: List[float] = []
    relative_values: List[float] = []
    confidence_values: List[float] = []

    for item in uncertainty_values:

        valid, errors = item.validate()

        if not valid:
            raise ValueError(
                "Invalid uncertainty item: "
                + "; ".join(errors)
            )

        if item.uncertainty is not None:

            absolute_values.append(
                abs(float(item.uncertainty))
            )

        relative = item.relative_uncertainty()

        if relative is not None:
            relative_values.append(relative)

        if item.confidence is not None:
            confidence_values.append(
                clamp(float(item.confidence))
            )

    count = len(uncertainty_values)

    coverage = (
        len(absolute_values) / count
    )

    mean_absolute = (
        sum(absolute_values) / len(absolute_values)
        if absolute_values
        else None
    )

    median_absolute = (
        _median(absolute_values)
        if absolute_values
        else None
    )

    max_absolute = (
        max(absolute_values)
        if absolute_values
        else None
    )

    mean_relative = (
        sum(relative_values) / len(relative_values)
        if relative_values
        else None
    )

    confidence = (
        sum(confidence_values) / len(confidence_values)
        if confidence_values
        else None
    )

    return UncertaintySummary(
        count=count,
        mean_absolute_uncertainty=mean_absolute,
        median_absolute_uncertainty=median_absolute,
        max_absolute_uncertainty=max_absolute,
        mean_relative_uncertainty=mean_relative,
        coverage=coverage,
        confidence=confidence,
        confidence_level=confidence_level_from_score(
            confidence
        ),
    )


# ============================================================
# METRIC-SET COMPATIBILITY
# ============================================================

def uncertainty_from_metric(
    metric_name: str,
    value: float,
    uncertainty: Optional[float],
    confidence: Optional[float] = None,
    unit: Optional[str] = None,
    source: UncertaintySource = (
        UncertaintySource.COMPUTATIONAL
    ),
) -> UncertaintyValue:
    """
    Convenience constructor for compatibility with
    the public metrics layer.

    Example metric names:
        entropy
        variance
        gradient
        coupling
        transition_index

    No proprietary interpretation is assigned.
    """

    return create_uncertainty(
        value=value,
        uncertainty=uncertainty,
        uncertainty_type=(
            UncertaintyType.STANDARD_DEVIATION
            if uncertainty is not None
            else UncertaintyType.UNKNOWN
        ),
        source=source,
        confidence=confidence,
        unit=unit,
        claim_class=ClaimClass.C2,
        description=(
            f"Uncertainty representation for public "
            f"metric: {metric_name}"
        ),
        provenance={
            "metric_name": metric_name,
            "module": MODULE_NAME,
            "module_version": MODULE_VERSION,
        },
    )


# ============================================================
# UNCERTAINTY CONTRACT
# ============================================================

def uncertainty_contract() -> Dict[str, Any]:
    """
    Public machine-readable contract.
    """

    return {
        "module_name": MODULE_NAME,
        "module_version": MODULE_VERSION,
        "schema_version": UNCERTAINTY_SCHEMA_VERSION,

        "proprietary_algorithms_included":
            PROPRIETARY_ALGORITHMS_INCLUDED,

        "raw_data_modification_allowed":
            RAW_DATA_MODIFICATION_ALLOWED,

        "medical_diagnosis_supported":
            MEDICAL_DIAGNOSIS_SUPPORTED,

        "flight_certification_supported":
            FLIGHT_CERTIFICATION_SUPPORTED,

        "supported_types": [
            item.value
            for item in UncertaintyType
        ],

        "supported_sources": [
            item.value
            for item in UncertaintySource
        ],

        "claim_classes": [
            item.value
            for item in ClaimClass
        ],

        "notes": [
            "Uncertainty values are descriptive metadata.",
            "Confidence is not automatically a probability of correctness.",
            "Confidence labels are reporting conventions.",
            "Propagation assumes the caller's stated independence/weighting assumptions.",
            "No medical diagnosis is performed.",
            "No spacecraft flight certification is performed.",
            "Raw input data are not modified.",
        ],
    }


# ============================================================
# VALIDATION
# ============================================================

def validate_uncertainty_payload(
    payload: Any,
) -> Tuple[bool, List[str]]:
    """
    Validate an uncertainty object or dictionary.
    """

    if isinstance(payload, UncertaintyValue):
        return payload.validate()

    if not isinstance(payload, dict):
        return False, [
            "Payload must be UncertaintyValue or dict."
        ]

    errors: List[str] = []

    if "value" not in payload:
        errors.append("Missing required field: value.")

    if "uncertainty" in payload:
        uncertainty = payload["uncertainty"]

        if uncertainty is not None:

            if not is_finite_number(uncertainty):
                errors.append(
                    "uncertainty must be finite."
                )

            elif float(uncertainty) < 0:
                errors.append(
                    "uncertainty cannot be negative."
                )

    if "confidence" in payload:
        confidence = payload["confidence"]

        if confidence is not None:

            if not is_finite_number(confidence):
                errors.append(
                    "confidence must be finite."
                )

            elif not 0.0 <= float(confidence) <= 1.0:
                errors.append(
                    "confidence must be between 0 and 1."
                )

    return len(errors) == 0, errors


# ============================================================
# SELF TEST
# ============================================================

def run_uncertainty_test() -> Dict[str, Any]:
    """
    Internal module validation.
    """

    results: Dict[str, Any] = {}

    # --------------------------------------------------------
    # Test 1: Basic uncertainty
    # --------------------------------------------------------

    item = create_uncertainty(
        value=10.0,
        uncertainty=0.5,
        uncertainty_type=(
            UncertaintyType.STANDARD_DEVIATION
        ),
        source=UncertaintySource.MEASUREMENT,
        confidence=0.90,
        unit="unit",
        description="Synthetic test measurement",
    )

    results["basic_object"] = (
        item.validate()[0]
    )

    # --------------------------------------------------------
    # Test 2: Interval
    # --------------------------------------------------------

    interval = item.interval()

    results["interval_test"] = (
        interval == (9.5, 10.5)
    )

    # --------------------------------------------------------
    # Test 3: Relative uncertainty
    # --------------------------------------------------------

    relative = item.relative_uncertainty()

    results["relative_uncertainty_test"] = (
        relative is not None
        and abs(relative - 0.05) < 1e-12
    )

    # --------------------------------------------------------
    # Test 4: Confidence
    # --------------------------------------------------------

    results["confidence_level_test"] = (
        item.confidence_level
        == ConfidenceLevel.VERY_HIGH
    )

    # --------------------------------------------------------
    # Test 5: Independent propagation
    # --------------------------------------------------------

    propagated = propagate_independent_uncertainties(
        values=[1.0, 2.0, 3.0],
        uncertainties=[0.1, 0.2, 0.3],
    )

    expected = math.sqrt(
        0.1**2 + 0.2**2 + 0.3**2
    )

    results["propagation_test"] = (
        abs(propagated - expected) < 1e-12
    )

    # --------------------------------------------------------
    # Test 6: Relative interval
    # --------------------------------------------------------

    rel_interval = relative_interval(
        value=100.0,
        relative_uncertainty=0.10,
    )

    results["relative_interval_test"] = (
        rel_interval == (90.0, 110.0)
    )

    # --------------------------------------------------------
    # Test 7: Batch summary
    # --------------------------------------------------------

    items = [
        create_uncertainty(
            value=10.0,
            uncertainty=0.5,
            confidence=0.9,
        ),
        create_uncertainty(
            value=20.0,
            uncertainty=1.0,
            confidence=0.8,
        ),
        create_uncertainty(
            value=30.0,
            uncertainty=1.5,
            confidence=0.7,
        ),
    ]

    summary = summarize_uncertainties(items)

    results["summary_test"] = (
        summary.count == 3
        and summary.mean_absolute_uncertainty == 1.0
        and summary.coverage == 1.0
    )

    # --------------------------------------------------------
    # Test 8: Invalid negative uncertainty
    # --------------------------------------------------------

    try:

        create_uncertainty(
            value=10.0,
            uncertainty=-1.0,
        )

        results["negative_uncertainty_rejection"] = False

    except ValueError:

        results["negative_uncertainty_rejection"] = True

    # --------------------------------------------------------
    # Test 9: Confidence bounds
    # --------------------------------------------------------

    try:

        create_uncertainty(
            value=10.0,
            uncertainty=1.0,
            confidence=1.5,
        )

        results["invalid_confidence_rejection"] = False

    except ValueError:

        results["invalid_confidence_rejection"] = True

    # --------------------------------------------------------
    # Test 10: No proprietary algorithm
    # --------------------------------------------------------

    results["proprietary_algorithm_disabled"] = (
        PROPRIETARY_ALGORITHMS_INCLUDED is False
    )

    # --------------------------------------------------------
    # Test 11: Raw modification disabled
    # --------------------------------------------------------

    results["raw_modification_disabled"] = (
        RAW_DATA_MODIFICATION_ALLOWED is False
    )

    # --------------------------------------------------------
    # Test 12: Medical diagnosis disabled
    # --------------------------------------------------------

    results["medical_diagnosis_disabled"] = (
        MEDICAL_DIAGNOSIS_SUPPORTED is False
    )

    # --------------------------------------------------------
    # Test 13: Flight certification disabled
    # --------------------------------------------------------

    results["flight_certification_disabled"] = (
        FLIGHT_CERTIFICATION_SUPPORTED is False
    )

    # --------------------------------------------------------
    # Final status
    # --------------------------------------------------------

    results["all_tests_passed"] = all(
        results.values()
    )

    return results


# ============================================================
# MODULE INFORMATION
# ============================================================

def module_info() -> Dict[str, Any]:
    """
    Return module metadata and public contract.
    """

    return {
        "module": MODULE_NAME,
        "version": MODULE_VERSION,
        "schema_version": UNCERTAINTY_SCHEMA_VERSION,

        "purpose": (
            "Public uncertainty representation, "
            "confidence metadata, interval handling, "
            "and generic uncertainty propagation."
        ),

        "public_only": True,

        "proprietary_algorithms_included":
            PROPRIETARY_ALGORITHMS_INCLUDED,

        "raw_data_modification_allowed":
            RAW_DATA_MODIFICATION_ALLOWED,

        "medical_diagnosis_supported":
            MEDICAL_DIAGNOSIS_SUPPORTED,

        "flight_certification_supported":
            FLIGHT_CERTIFICATION_SUPPORTED,

        "claim_class": ClaimClass.C2.value,

        "contract": uncertainty_contract(),
    }


# ============================================================
# DIRECT EXECUTION TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("D³ VITAL-X | uncertainty.py")
    print("=" * 60)

    test_results = run_uncertainty_test()

    for key, value in test_results.items():
        print(f"{key}: {value}")

    print("-" * 60)

    if test_results["all_tests_passed"]:
        print("✅ ALL UNCERTAINTY TESTS PASSED")
    else:
        print("❌ SOME UNCERTAINTY TESTS FAILED")

    print("=" * 60)
