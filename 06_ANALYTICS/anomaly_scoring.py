# ============================================================
# D³ VITAL-X Space Intelligence Platform
# Module 20 — anomaly_scoring.py
# ============================================================
#
# PUBLIC ANOMALY SCORING / PRIORITIZATION LAYER
#
# ============================================================
# SECURITY / ARCHITECTURE PRINCIPLES
# ============================================================
#
# This module is intentionally a PUBLIC anomaly-prioritization
# layer.
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
#   ❌ disease probability
#   ❌ flight certification
#
# It ONLY:
#
#   1. accepts public numerical features / metrics
#   2. validates finite numerical values
#   3. establishes a transparent reference distribution
#   4. calculates generic deviation scores
#   5. combines public deviation components
#   6. produces an anomaly-prioritization score
#   7. records quality and provenance
#   8. preserves C2 claim classification
#   9. requires human review
#
# IMPORTANT:
#
# "Anomaly" in this module means:
#
#   statistical unusualness relative to the supplied
#   reference data/configuration.
#
# It does NOT mean:
#
#   - disease
#   - injury
#   - spacecraft failure
#   - extraterrestrial technology
#   - new physical law
#   - causal mechanism
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple
import hashlib
import json
import math
import statistics
import uuid


# ============================================================
# MODULE METADATA
# ============================================================

MODULE_NAME = "anomaly_scoring"
MODULE_VERSION = "1.0.0"
ANOMALY_SCHEMA_VERSION = "1.0"

PROPRIETARY_ALGORITHMS_INCLUDED = False
RAW_DATA_MODIFICATION_ALLOWED = False
MEDICAL_DIAGNOSIS_SUPPORTED = False
FLIGHT_CERTIFICATION_SUPPORTED = False

# Anomaly score is explicitly a research prioritization result.
CLAIM_CLASS = "C2"
HUMAN_REVIEW_REQUIRED = True


# ============================================================
# ENUMS
# ============================================================

class AnomalyQuality(str, Enum):
    """
    Public quality state.

    This is NOT a scientific significance judgment.
    """

    VALID = "VALID"
    INVALID = "INVALID"
    MISSING = "MISSING"
    NONFINITE = "NONFINITE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    LOW_QUALITY = "LOW_QUALITY"
    UNVERIFIED = "UNVERIFIED"


class AnomalyLevel(str, Enum):
    """
    Descriptive prioritization level.

    These labels do NOT represent medical, physical, or
    operational severity.
    """

    NORMAL_RANGE = "NORMAL_RANGE"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"
    UNVERIFIED = "UNVERIFIED"


class ReferenceMethod(str, Enum):
    """
    Transparent public reference-distribution methods.
    """

    Z_SCORE = "Z_SCORE"
    ROBUST_Z_SCORE = "ROBUST_Z_SCORE"
    MIN_MAX = "MIN_MAX"


class ClaimClass(str, Enum):

    C1 = "C1"
    C2 = "C2"
    C3 = "C3"


# ============================================================
# SAFE UTILITIES
# ============================================================

def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_anomaly_id() -> str:
    return f"anomaly-{uuid.uuid4().hex}"


def generate_analysis_id() -> str:
    return f"anomaly-analysis-{uuid.uuid4().hex}"


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


def finite_values(
    values: Sequence[Any],
) -> Tuple[List[float], List[int]]:

    valid: List[float] = []
    invalid_indices: List[int] = []

    for index, value in enumerate(values):

        if is_finite_number(value):
            valid.append(float(value))
        else:
            invalid_indices.append(index)

    return valid, invalid_indices


def mean_safe(
    values: Sequence[float],
) -> Optional[float]:

    if not values:
        return None

    return float(statistics.fmean(values))


def standard_deviation_safe(
    values: Sequence[float],
) -> Optional[float]:

    if len(values) < 2:
        return None

    return float(
        statistics.pstdev(values)
    )


def median_safe(
    values: Sequence[float],
) -> Optional[float]:

    if not values:
        return None

    return float(
        statistics.median(values)
    )


def median_absolute_deviation(
    values: Sequence[float],
) -> Optional[float]:

    if not values:
        return None

    median = statistics.median(values)

    deviations = [
        abs(value - median)
        for value in values
    ]

    return float(
        statistics.median(deviations)
    )


def clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 1.0,
) -> float:

    return float(
        min(
            max(value, minimum),
            maximum,
        )
    )


# ============================================================
# ANOMALY CONFIGURATION
# ============================================================

@dataclass(frozen=True)
class AnomalyScoringConfig:
    """
    Transparent configuration for generic anomaly scoring.

    No proprietary coefficient or model weight is embedded.
    """

    reference_method: ReferenceMethod = (
        ReferenceMethod.ROBUST_Z_SCORE
    )

    minimum_reference_size: int = 5

    normal_threshold: float = 1.0

    elevated_threshold: float = 2.0

    high_threshold: float = 3.0

    score_scale: float = 3.0

    weight_mode: str = "EQUAL"

    default_weight: float = 1.0

    claim_class: ClaimClass = ClaimClass.C2

    human_review_required: bool = True

    def validate(self) -> Tuple[bool, List[str]]:

        errors: List[str] = []

        if not isinstance(
            self.reference_method,
            ReferenceMethod,
        ):
            errors.append(
                "Invalid reference method."
            )

        if self.minimum_reference_size < 2:
            errors.append(
                "minimum_reference_size must be >= 2."
            )

        thresholds = {
            "normal_threshold": (
                self.normal_threshold
            ),
            "elevated_threshold": (
                self.elevated_threshold
            ),
            "high_threshold": (
                self.high_threshold
            ),
            "score_scale": self.score_scale,
            "default_weight": self.default_weight,
        }

        for name, value in thresholds.items():

            if not is_finite_number(value):

                errors.append(
                    f"{name} must be finite."
                )

            elif name != "default_weight" and value < 0:

                errors.append(
                    f"{name} cannot be negative."
                )

        if not (
            self.normal_threshold
            <= self.elevated_threshold
            <= self.high_threshold
        ):

            errors.append(
                "Thresholds must satisfy "
                "normal <= elevated <= high."
            )

        if self.score_scale <= 0:

            errors.append(
                "score_scale must be > 0."
            )

        if self.default_weight < 0:

            errors.append(
                "default_weight cannot be negative."
            )

        if self.weight_mode not in {
            "EQUAL",
            "CUSTOM",
        }:

            errors.append(
                "weight_mode must be EQUAL or CUSTOM."
            )

        if not isinstance(
            self.claim_class,
            ClaimClass,
        ):

            errors.append(
                "Invalid claim class."
            )

        return len(errors) == 0, errors


# ============================================================
# REFERENCE STATISTICS
# ============================================================

@dataclass
class ReferenceStatistics:
    """
    Public descriptive statistics used as the anomaly
    reference distribution.
    """

    feature_name: str

    method: ReferenceMethod

    count: int

    mean: Optional[float]

    standard_deviation: Optional[float]

    median: Optional[float]

    mad: Optional[float]

    minimum: Optional[float]

    maximum: Optional[float]

    quality: AnomalyQuality = (
        AnomalyQuality.UNVERIFIED
    )

    def validate(self) -> Tuple[bool, List[str]]:

        errors: List[str] = []

        if not self.feature_name:
            errors.append(
                "feature_name is required."
            )

        if self.count < 0:
            errors.append(
                "Reference count cannot be negative."
            )

        numeric_fields = {
            "mean": self.mean,
            "standard_deviation": (
                self.standard_deviation
            ),
            "median": self.median,
            "mad": self.mad,
            "minimum": self.minimum,
            "maximum": self.maximum,
        }

        for name, value in numeric_fields.items():

            if value is not None and not is_finite_number(
                value
            ):

                errors.append(
                    f"{name} must be finite when present."
                )

        return len(errors) == 0, errors

    def to_dict(self) -> Dict[str, Any]:

        result = asdict(self)

        result["method"] = self.method.value
        result["quality"] = self.quality.value

        return result


def build_reference_statistics(
    values: Sequence[Any],
    feature_name: str,
    method: ReferenceMethod,
    minimum_reference_size: int = 5,
) -> ReferenceStatistics:

    valid_values, invalid_indices = (
        finite_values(values)
    )

    count = len(valid_values)

    if count == 0:

        return ReferenceStatistics(
            feature_name=sanitize_identifier(
                feature_name,
                "feature",
            ),
            method=method,
            count=0,
            mean=None,
            standard_deviation=None,
            median=None,
            mad=None,
            minimum=None,
            maximum=None,
            quality=AnomalyQuality.NONFINITE,
        )

    if count < minimum_reference_size:

        quality = (
            AnomalyQuality.INSUFFICIENT_DATA
        )

    elif invalid_indices:

        quality = AnomalyQuality.LOW_QUALITY

    else:

        quality = AnomalyQuality.VALID

    return ReferenceStatistics(
        feature_name=sanitize_identifier(
            feature_name,
            "feature",
        ),
        method=method,
        count=count,
        mean=mean_safe(valid_values),
        standard_deviation=(
            standard_deviation_safe(
                valid_values
            )
        ),
        median=median_safe(
            valid_values
        ),
        mad=median_absolute_deviation(
            valid_values
        ),
        minimum=min(valid_values),
        maximum=max(valid_values),
        quality=quality,
    )


# ============================================================
# SINGLE FEATURE ANOMALY RESULT
# ============================================================

@dataclass
class FeatureAnomalyResult:
    """
    Public anomaly result for one feature.

    The score is a statistical prioritization value, not
    a probability of disease, failure, or physical cause.
    """

    anomaly_id: str

    feature_name: str

    value: Optional[float]

    standardized_deviation: Optional[float]

    absolute_deviation: Optional[float]

    normalized_score: Optional[float]

    level: AnomalyLevel

    quality: AnomalyQuality

    reference: ReferenceStatistics

    weight: float = 1.0

    claim_class: ClaimClass = ClaimClass.C2

    human_review_required: bool = True

    source_dataset_id: Optional[str] = None

    provenance: Dict[str, Any] = field(
        default_factory=dict
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    timestamp: str = field(
        default_factory=utc_timestamp
    )

    def validate(self) -> Tuple[bool, List[str]]:

        errors: List[str] = []

        if not self.anomaly_id:
            errors.append(
                "anomaly_id is required."
            )

        if not self.feature_name:
            errors.append(
                "feature_name is required."
            )

        numeric_fields = {
            "value": self.value,
            "standardized_deviation": (
                self.standardized_deviation
            ),
            "absolute_deviation": (
                self.absolute_deviation
            ),
            "normalized_score": (
                self.normalized_score
            ),
            "weight": self.weight,
        }

        for name, value in numeric_fields.items():

            if value is not None and not is_finite_number(
                value
            ):

                errors.append(
                    f"{name} must be finite when present."
                )

        if self.normalized_score is not None:

            if not (
                0.0
                <= self.normalized_score
                <= 1.0
            ):

                errors.append(
                    "normalized_score must be between 0 and 1."
                )

        if self.weight < 0:

            errors.append(
                "weight cannot be negative."
            )

        if not isinstance(
            self.level,
            AnomalyLevel,
        ):

            errors.append(
                "Invalid anomaly level."
            )

        if not isinstance(
            self.quality,
            AnomalyQuality,
        ):

            errors.append(
                "Invalid anomaly quality."
            )

        if not isinstance(
            self.claim_class,
            ClaimClass,
        ):

            errors.append(
                "Invalid claim class."
            )

        reference_valid, reference_errors = (
            self.reference.validate()
        )

        if not reference_valid:
            errors.extend(
                reference_errors
            )

        return len(errors) == 0, errors

    def fingerprint(self) -> str:

        payload = {
            "anomaly_id": self.anomaly_id,
            "feature_name": self.feature_name,
            "value": self.value,
            "standardized_deviation": (
                self.standardized_deviation
            ),
            "absolute_deviation": (
                self.absolute_deviation
            ),
            "normalized_score": (
                self.normalized_score
            ),
            "level": self.level.value,
            "quality": self.quality.value,
            "reference": (
                self.reference.to_dict()
            ),
            "weight": self.weight,
            "claim_class": (
                self.claim_class.value
            ),
        }

        return calculate_sha256(payload)

    def to_dict(self) -> Dict[str, Any]:

        result = asdict(self)

        result["level"] = self.level.value
        result["quality"] = self.quality.value
        result["claim_class"] = (
            self.claim_class.value
        )

        result["reference"] = (
            self.reference.to_dict()
        )

        result["fingerprint"] = (
            self.fingerprint()
        )

        return result


# ============================================================
# STANDARDIZED DEVIATION
# ============================================================

def calculate_z_score(
    value: float,
    reference: ReferenceStatistics,
) -> Optional[float]:

    if reference.mean is None:
        return None

    if reference.standard_deviation is None:
        return None

    if reference.standard_deviation <= 0:
        return None

    return float(
        (
            value
            - reference.mean
        )
        / reference.standard_deviation
    )


def calculate_robust_z_score(
    value: float,
    reference: ReferenceStatistics,
) -> Optional[float]:

    if reference.median is None:
        return None

    if reference.mad is None:
        return None

    if reference.mad <= 0:
        return None

    # Standard normal consistency factor.
    robust_scale = (
        1.4826
        * reference.mad
    )

    if robust_scale <= 0:
        return None

    return float(
        (
            value
            - reference.median
        )
        / robust_scale
    )


def calculate_min_max_score(
    value: float,
    reference: ReferenceStatistics,
) -> Optional[float]:

    if (
        reference.minimum is None
        or reference.maximum is None
    ):
        return None

    denominator = (
        reference.maximum
        - reference.minimum
    )

    if denominator <= 0:
        return 0.0

    distance = min(
        abs(value - reference.minimum),
        abs(value - reference.maximum),
    )

    # For values inside the reference range, this score
    # represents relative distance from the nearest boundary.
    if (
        reference.minimum
        <= value
        <= reference.maximum
    ):

        distance_from_nearest_boundary = min(
            value - reference.minimum,
            reference.maximum - value,
        )

        return clamp(
            1.0
            - (
                distance_from_nearest_boundary
                / denominator
            )
        )

    return clamp(
        1.0
        + (
            abs(
                value
                - (
                    reference.maximum
                    if value > reference.maximum
                    else reference.minimum
                )
            )
            / denominator
        ),
        0.0,
        10.0,
    )


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_deviation(
    standardized_deviation: Optional[float],
    score_scale: float = 3.0,
) -> Optional[float]:

    if standardized_deviation is None:
        return None

    if not is_finite_number(
        standardized_deviation
    ):
        return None

    if score_scale <= 0:
        return None

    magnitude = abs(
        float(standardized_deviation)
    )

    return clamp(
        magnitude / score_scale,
        0.0,
        1.0,
    )


# ============================================================
# LEVEL CLASSIFICATION
# ============================================================

def classify_anomaly_level(
    standardized_deviation: Optional[float],
    config: AnomalyScoringConfig,
) -> AnomalyLevel:

    if standardized_deviation is None:

        return AnomalyLevel.UNVERIFIED

    magnitude = abs(
        float(standardized_deviation)
    )

    if magnitude < config.normal_threshold:

        return AnomalyLevel.NORMAL_RANGE

    if magnitude < config.elevated_threshold:

        return AnomalyLevel.ELEVATED

    return AnomalyLevel.HIGH


# ============================================================
# SINGLE FEATURE SCORING
# ============================================================

def score_feature(
    value: Any,
    reference: ReferenceStatistics,
    *,
    config: Optional[AnomalyScoringConfig] = None,
    weight: Optional[float] = None,
    source_dataset_id: Optional[str] = None,
    provenance: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> FeatureAnomalyResult:

    if config is None:
        config = AnomalyScoringConfig()

    config_valid, config_errors = (
        config.validate()
    )

    if not config_valid:

        raise ValueError(
            "Invalid AnomalyScoringConfig: "
            + " | ".join(config_errors)
        )

    feature_name = (
        reference.feature_name
    )

    actual_weight = (
        config.default_weight
        if weight is None
        else float(weight)
    )

    if actual_weight < 0:

        raise ValueError(
            "Feature weight cannot be negative."
        )

    # --------------------------------------------------------
    # Missing value
    # --------------------------------------------------------

    if value is None:

        return FeatureAnomalyResult(
            anomaly_id=generate_anomaly_id(),
            feature_name=feature_name,
            value=None,
            standardized_deviation=None,
            absolute_deviation=None,
            normalized_score=None,
            level=AnomalyLevel.UNVERIFIED,
            quality=AnomalyQuality.MISSING,
            reference=reference,
            weight=actual_weight,
            claim_class=config.claim_class,
            human_review_required=(
                config.human_review_required
            ),
            source_dataset_id=source_dataset_id,
            provenance=provenance or {},
            metadata=metadata or {},
        )

    # --------------------------------------------------------
    # Non-finite value
    # --------------------------------------------------------

    if not is_finite_number(value):

        return FeatureAnomalyResult(
            anomaly_id=generate_anomaly_id(),
            feature_name=feature_name,
            value=None,
            standardized_deviation=None,
            absolute_deviation=None,
            normalized_score=None,
            level=AnomalyLevel.UNVERIFIED,
            quality=AnomalyQuality.NONFINITE,
            reference=reference,
            weight=actual_weight,
            claim_class=config.claim_class,
            human_review_required=(
                config.human_review_required
            ),
            source_dataset_id=source_dataset_id,
            provenance=provenance or {},
            metadata=metadata or {},
        )

    numeric_value = float(value)

    # --------------------------------------------------------
    # Reference quality
    # --------------------------------------------------------

    if reference.count < (
        config.minimum_reference_size
    ):

        return FeatureAnomalyResult(
            anomaly_id=generate_anomaly_id(),
            feature_name=feature_name,
            value=numeric_value,
            standardized_deviation=None,
            absolute_deviation=None,
            normalized_score=None,
            level=AnomalyLevel.UNVERIFIED,
            quality=AnomalyQuality.INSUFFICIENT_DATA,
            reference=reference,
            weight=actual_weight,
            claim_class=config.claim_class,
            human_review_required=(
                config.human_review_required
            ),
            source_dataset_id=source_dataset_id,
            provenance=provenance or {},
            metadata=metadata or {},
        )

    # --------------------------------------------------------
    # Standardized deviation
    # --------------------------------------------------------

    if (
        config.reference_method
        == ReferenceMethod.Z_SCORE
    ):

        standardized_deviation = (
            calculate_z_score(
                numeric_value,
                reference,
            )
        )

    elif (
        config.reference_method
        == ReferenceMethod.ROBUST_Z_SCORE
    ):

        standardized_deviation = (
            calculate_robust_z_score(
                numeric_value,
                reference,
            )
        )

    elif (
        config.reference_method
        == ReferenceMethod.MIN_MAX
    ):

        minmax = calculate_min_max_score(
            numeric_value,
            reference,
        )

        if minmax is None:

            standardized_deviation = None

        else:

            standardized_deviation = (
                minmax
                * config.score_scale
            )

    else:

        standardized_deviation = None

    # --------------------------------------------------------
    # Absolute deviation
    # --------------------------------------------------------

    center = (
        reference.median
        if (
            config.reference_method
            == ReferenceMethod.ROBUST_Z_SCORE
        )
        else reference.mean
    )

    absolute_deviation = None

    if center is not None:

        absolute_deviation = abs(
            numeric_value
            - center
        )

    # --------------------------------------------------------
    # Normalized score
    # --------------------------------------------------------

    normalized_score = (
        normalize_deviation(
            standardized_deviation,
            config.score_scale,
        )
    )

    # --------------------------------------------------------
    # Quality
    # --------------------------------------------------------

    if standardized_deviation is None:

        quality = AnomalyQuality.UNVERIFIED

    elif reference.quality == (
        AnomalyQuality.LOW_QUALITY
    ):

        quality = AnomalyQuality.LOW_QUALITY

    elif reference.quality != (
        AnomalyQuality.VALID
    ):

        quality = reference.quality

    else:

        quality = AnomalyQuality.VALID

    level = classify_anomaly_level(
        standardized_deviation,
        config,
    )

    return FeatureAnomalyResult(
        anomaly_id=generate_anomaly_id(),
        feature_name=feature_name,
        value=numeric_value,
        standardized_deviation=(
            standardized_deviation
        ),
        absolute_deviation=(
            absolute_deviation
        ),
        normalized_score=normalized_score,
        level=level,
        quality=quality,
        reference=reference,
        weight=actual_weight,
        claim_class=config.claim_class,
        human_review_required=(
            config.human_review_required
        ),
        source_dataset_id=source_dataset_id,
        provenance=provenance or {},
        metadata=metadata or {},
    )


# ============================================================
# MULTI-FEATURE ANOMALY RESULT
# ============================================================

@dataclass
class AnomalyAnalysisResult:
    """
    Collection of public anomaly-prioritization results.
    """

    analysis_id: str

    source_dataset_id: Optional[str]

    feature_results: List[
        FeatureAnomalyResult
    ] = field(default_factory=list)

    aggregate_score: Optional[float] = None

    level: AnomalyLevel = (
        AnomalyLevel.UNVERIFIED
    )

    quality: AnomalyQuality = (
        AnomalyQuality.UNVERIFIED
    )

    claim_class: ClaimClass = ClaimClass.C2

    human_review_required: bool = True

    provenance: Dict[str, Any] = field(
        default_factory=dict
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    created_at: str = field(
        default_factory=utc_timestamp
    )

    def validate(self) -> Tuple[bool, List[str]]:

        errors: List[str] = []

        if not self.analysis_id:
            errors.append(
                "analysis_id is required."
            )

        for result in self.feature_results:

            valid, result_errors = (
                result.validate()
            )

            if not valid:
                errors.extend(
                    result_errors
                )

        if self.aggregate_score is not None:

            if not is_finite_number(
                self.aggregate_score
            ):

                errors.append(
                    "aggregate_score must be finite."
                )

            elif not (
                0.0
                <= self.aggregate_score
                <= 1.0
            ):

                errors.append(
                    "aggregate_score must be between 0 and 1."
                )

        if not isinstance(
            self.level,
            AnomalyLevel,
        ):

            errors.append(
                "Invalid anomaly level."
            )

        if not isinstance(
            self.quality,
            AnomalyQuality,
        ):

            errors.append(
                "Invalid anomaly quality."
            )

        return len(errors) == 0, errors

    def valid_results(
        self,
    ) -> List[FeatureAnomalyResult]:

        return [
            result
            for result in self.feature_results
            if (
                result.quality
                == AnomalyQuality.VALID
                and result.normalized_score
                is not None
            )
        ]

    def fingerprint(self) -> str:

        payload = {
            "analysis_id": self.analysis_id,
            "source_dataset_id": (
                self.source_dataset_id
            ),
            "feature_results": [
                result.fingerprint()
                for result in self.feature_results
            ],
            "aggregate_score": (
                self.aggregate_score
            ),
            "level": self.level.value,
            "quality": self.quality.value,
            "claim_class": (
                self.claim_class.value
            ),
        }

        return calculate_sha256(payload)

    def to_dict(self) -> Dict[str, Any]:

        return {
            "analysis_id": self.analysis_id,
            "source_dataset_id": (
                self.source_dataset_id
            ),
            "feature_results": [
                result.to_dict()
                for result in self.feature_results
            ],
            "aggregate_score": (
                self.aggregate_score
            ),
            "level": self.level.value,
            "quality": self.quality.value,
            "claim_class": (
                self.claim_class.value
            ),
            "human_review_required": (
                self.human_review_required
            ),
            "provenance": self.provenance,
            "metadata": self.metadata,
            "created_at": self.created_at,
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
# AGGREGATE SCORING
# ============================================================

def aggregate_anomaly_scores(
    results: Sequence[FeatureAnomalyResult],
) -> Optional[float]:

    weighted_scores: List[Tuple[
        float,
        float,
    ]] = []

    for result in results:

        if result.quality != (
            AnomalyQuality.VALID
        ):
            continue

        if result.normalized_score is None:
            continue

        if result.weight <= 0:
            continue

        weighted_scores.append(
            (
                float(result.normalized_score),
                float(result.weight),
            )
        )

    if not weighted_scores:
        return None

    numerator = sum(
        score * weight
        for score, weight
        in weighted_scores
    )

    denominator = sum(
        weight
        for _, weight
        in weighted_scores
    )

    if denominator <= 0:
        return None

    return clamp(
        numerator / denominator,
        0.0,
        1.0,
    )


def classify_aggregate_level(
    aggregate_score: Optional[float],
) -> AnomalyLevel:

    if aggregate_score is None:
        return AnomalyLevel.UNVERIFIED

    # The aggregate score is normalized to [0, 1].
    if aggregate_score < (
        1.0 / 3.0
    ):

        return AnomalyLevel.NORMAL_RANGE

    if aggregate_score < (
        2.0 / 3.0
    ):

        return AnomalyLevel.ELEVATED

    return AnomalyLevel.HIGH


# ============================================================
# MULTI-FEATURE ANALYSIS
# ============================================================

def analyze_features(
    feature_values: Dict[str, Any],
    references: Dict[str, ReferenceStatistics],
    *,
    config: Optional[AnomalyScoringConfig] = None,
    weights: Optional[Dict[str, float]] = None,
    source_dataset_id: Optional[str] = None,
    provenance: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AnomalyAnalysisResult:

    if config is None:
        config = AnomalyScoringConfig()

    config_valid, config_errors = (
        config.validate()
    )

    if not config_valid:

        raise ValueError(
            "Invalid AnomalyScoringConfig: "
            + " | ".join(config_errors)
        )

    weights = weights or {}

    results: List[
        FeatureAnomalyResult
    ] = []

    for feature_name, value in (
        feature_values.items()
    ):

        reference = references.get(
            feature_name
        )

        if reference is None:

            # Unknown reference is explicitly recorded
            # rather than silently calculated.
            reference = ReferenceStatistics(
                feature_name=feature_name,
                method=(
                    config.reference_method
                ),
                count=0,
                mean=None,
                standard_deviation=None,
                median=None,
                mad=None,
                minimum=None,
                maximum=None,
                quality=(
                    AnomalyQuality.INSUFFICIENT_DATA
                ),
            )

        result = score_feature(
            value,
            reference,
            config=config,
            weight=weights.get(
                feature_name,
                config.default_weight,
            ),
            source_dataset_id=(
                source_dataset_id
            ),
            provenance=(
                provenance or {}
            ),
            metadata=(
                metadata or {}
            ),
        )

        results.append(result)

    aggregate_score = (
        aggregate_anomaly_scores(
            results
        )
    )

    if aggregate_score is None:

        aggregate_level = (
            AnomalyLevel.UNVERIFIED
        )

        aggregate_quality = (
            AnomalyQuality.INSUFFICIENT_DATA
        )

    else:

        aggregate_level = (
            classify_aggregate_level(
                aggregate_score
            )
        )

        valid_results = [
            result
            for result in results
            if (
                result.quality
                == AnomalyQuality.VALID
            )
        ]

        if len(valid_results) == len(
            results
        ):

            aggregate_quality = (
                AnomalyQuality.VALID
            )

        else:

            aggregate_quality = (
                AnomalyQuality.LOW_QUALITY
            )

    result_metadata = {
        **(
            metadata or {}
        ),
        "raw_data_modified": False,
        "scoring_policy": (
            "Generic statistical deviation "
            "relative to a supplied reference "
            "distribution."
        ),
        "interpretation_policy": (
            "Anomaly score is a research "
            "prioritization signal only."
        ),
    }

    return AnomalyAnalysisResult(
        analysis_id=generate_analysis_id(),
        source_dataset_id=(
            source_dataset_id
        ),
        feature_results=results,
        aggregate_score=aggregate_score,
        level=aggregate_level,
        quality=aggregate_quality,
        claim_class=config.claim_class,
        human_review_required=(
            config.human_review_required
        ),
        provenance=provenance or {},
        metadata=result_metadata,
    )


# ============================================================
# SERIES ANOMALY ANALYSIS
# ============================================================

def analyze_series_anomalies(
    values: Sequence[Any],
    *,
    feature_name: str = "metric",
    reference_values: Optional[
        Sequence[Any]
    ] = None,
    config: Optional[AnomalyScoringConfig] = None,
    source_dataset_id: Optional[str] = None,
    provenance: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> List[FeatureAnomalyResult]:

    if config is None:
        config = AnomalyScoringConfig()

    if reference_values is None:
        reference_values = values

    reference = build_reference_statistics(
        reference_values,
        feature_name,
        config.reference_method,
        config.minimum_reference_size,
    )

    results: List[
        FeatureAnomalyResult
    ] = []

    for value in values:

        result = score_feature(
            value,
            reference,
            config=config,
            source_dataset_id=(
                source_dataset_id
            ),
            provenance=(
                provenance or {}
            ),
            metadata=(
                metadata or {}
            ),
        )

        results.append(result)

    return results


# ============================================================
# SUMMARY
# ============================================================

def summarize_anomaly_analysis(
    result: AnomalyAnalysisResult,
) -> Dict[str, Any]:

    level_summary = {
        level.value: 0
        for level in AnomalyLevel
    }

    quality_summary = {
        quality.value: 0
        for quality in AnomalyQuality
    }

    for feature_result in (
        result.feature_results
    ):

        level_summary[
            feature_result.level.value
        ] += 1

        quality_summary[
            feature_result.quality.value
        ] += 1

    return {
        "analysis_id": result.analysis_id,
        "source_dataset_id": (
            result.source_dataset_id
        ),
        "feature_count": len(
            result.feature_results
        ),
        "aggregate_anomaly_score": (
            result.aggregate_score
        ),
        "aggregate_level": (
            result.level.value
        ),
        "quality": (
            result.quality.value
        ),
        "claim_class": (
            result.claim_class.value
        ),
        "human_review_required": (
            result.human_review_required
        ),
        "level_summary": level_summary,
        "quality_summary": quality_summary,
        "fingerprint": (
            result.fingerprint()
        ),
    }


# ============================================================
# PUBLIC PAYLOAD VALIDATION
# ============================================================

def validate_anomaly_payload(
    payload: Dict[str, Any],
) -> Tuple[bool, List[str]]:

    errors: List[str] = []

    if not isinstance(
        payload,
        dict,
    ):

        return (
            False,
            [
                "Anomaly payload must be a dictionary."
            ],
        )

    feature_name = payload.get(
        "feature_name"
    )

    if not feature_name:

        errors.append(
            "feature_name is required."
        )

    numeric_fields = [
        "value",
        "standardized_deviation",
        "absolute_deviation",
        "normalized_score",
        "weight",
    ]

    for field_name in numeric_fields:

        value = payload.get(
            field_name
        )

        if value is not None and not is_finite_number(
            value
        ):

            errors.append(
                f"{field_name} must be finite."
            )

    normalized_score = payload.get(
        "normalized_score"
    )

    if normalized_score is not None:

        if not (
            0.0
            <= float(normalized_score)
            <= 1.0
        ):

            errors.append(
                "normalized_score must be between 0 and 1."
            )

    weight = payload.get(
        "weight"
    )

    if weight is not None:

        if float(weight) < 0:

            errors.append(
                "weight cannot be negative."
            )

    level = payload.get(
        "level"
    )

    if level is not None:

        valid_levels = {
            item.value
            for item in AnomalyLevel
        }

        if str(level) not in valid_levels:

            errors.append(
                "Invalid anomaly level."
            )

    quality = payload.get(
        "quality"
    )

    if quality is not None:

        valid_quality = {
            item.value
            for item in AnomalyQuality
        }

        if str(quality) not in valid_quality:

            errors.append(
                "Invalid anomaly quality."
            )

    return (
        len(errors) == 0,
        errors,
    )


# ============================================================
# PUBLIC CONTRACT
# ============================================================

def anomaly_scoring_contract() -> Dict[str, Any]:

    return {
        "module": MODULE_NAME,
        "version": MODULE_VERSION,
        "schema_version": (
            ANOMALY_SCHEMA_VERSION
        ),

        "purpose": (
            "Public statistical anomaly scoring "
            "and research prioritization."
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

        "claim_class": (
            CLAIM_CLASS
        ),

        "human_review_required": (
            HUMAN_REVIEW_REQUIRED
        ),

        "interpretation_policy": (
            "Anomaly scores represent statistical "
            "unusualness relative to a supplied "
            "reference distribution."
        ),

        "medical_policy": (
            "Anomaly scoring does not diagnose "
            "disease or injury."
        ),

        "spaceflight_policy": (
            "Anomaly scoring does not certify "
            "spacecraft or astronaut safety."
        ),

        "private_engine_policy": (
            "No proprietary engine implementation, "
            "model weights, or private coefficients "
            "are included."
        ),
    }


# ============================================================
# MODULE INFO
# ============================================================

def module_info() -> Dict[str, Any]:

    return {
        "module_name": MODULE_NAME,
        "module_version": MODULE_VERSION,
        "schema_version": (
            ANOMALY_SCHEMA_VERSION
        ),

        "role": (
            "Public statistical anomaly "
            "prioritization layer."
        ),

        "proprietary_algorithm_included": False,
        "raw_data_modification": False,
        "medical_diagnosis": False,
        "flight_certification": False,

        "claim_class": CLAIM_CLASS,

        "human_review_required": (
            HUMAN_REVIEW_REQUIRED
        ),

        "supported_reference_methods": [
            method.value
            for method in ReferenceMethod
        ],

        "supported_outputs": [
            "reference_statistics",
            "standardized_deviation",
            "absolute_deviation",
            "normalized_score",
            "anomaly_level",
            "aggregate_anomaly_score",
            "quality_state",
            "provenance",
            "fingerprint",
        ],
    }


# ============================================================
# SECURITY / ARCHITECTURE SELF-TEST
# ============================================================

def run_anomaly_scoring_test() -> Dict[str, Any]:

    results: Dict[str, Any] = {}

    # --------------------------------------------------------
    # Configuration
    # --------------------------------------------------------

    config = AnomalyScoringConfig(
        reference_method=(
            ReferenceMethod.ROBUST_Z_SCORE
        ),
        minimum_reference_size=5,
        normal_threshold=1.0,
        elevated_threshold=2.0,
        high_threshold=3.0,
    )

    config_valid, config_errors = (
        config.validate()
    )

    results["config_valid"] = (
        config_valid
    )

    # --------------------------------------------------------
    # Reference distribution
    # --------------------------------------------------------

    reference_values = [
        10.0,
        10.2,
        9.9,
        10.1,
        10.3,
        9.8,
        10.0,
        10.2,
        9.95,
        10.05,
    ]

    reference = (
        build_reference_statistics(
            reference_values,
            "signal_feature",
            config.reference_method,
            config.minimum_reference_size,
        )
    )

    results["reference_created"] = (
        reference.count
        == len(reference_values)
    )

    results["reference_valid"] = (
        reference.quality
        == AnomalyQuality.VALID
    )

    # --------------------------------------------------------
    # Normal observation
    # --------------------------------------------------------

    normal_result = score_feature(
        10.1,
        reference,
        config=config,
        source_dataset_id="TEST_DATASET",
    )

    results["normal_result_created"] = (
        isinstance(
            normal_result,
            FeatureAnomalyResult,
        )
    )

    results["normal_result_valid"] = (
        normal_result.quality
        == AnomalyQuality.VALID
    )

    # --------------------------------------------------------
    # Clearly shifted observation
    # --------------------------------------------------------

    high_result = score_feature(
        15.0,
        reference,
        config=config,
        source_dataset_id="TEST_DATASET",
    )

    results["deviation_detected"] = (
        high_result.standardized_deviation
        is not None
        and abs(
            high_result.standardized_deviation
        ) > 3.0
    )

    results["normalized_score_bounded"] = (
        high_result.normalized_score
        is not None
        and 0.0
        <= high_result.normalized_score
        <= 1.0
    )

    results["human_review_required"] = (
        high_result.human_review_required
        is True
    )

    results["high_level_assigned"] = (
        high_result.level
        == AnomalyLevel.HIGH
    )

    # --------------------------------------------------------
    # Multi-feature analysis
    # --------------------------------------------------------

    feature_values = {
        "entropy": 2.1,
        "variance": 1.5,
        "coupling": -0.91,
    }

    references = {
        "entropy": build_reference_statistics(
            [
                1.0,
                1.1,
                1.05,
                1.02,
                1.08,
                1.0,
                1.06,
                1.04,
            ],
            "entropy",
            config.reference_method,
            config.minimum_reference_size,
        ),

        "variance": build_reference_statistics(
            [
                1.0,
                1.1,
                0.95,
                1.02,
                1.05,
                0.98,
                1.01,
                1.03,
            ],
            "variance",
            config.reference_method,
            config.minimum_reference_size,
        ),

        "coupling": build_reference_statistics(
            [
                -0.10,
                -0.12,
                -0.08,
                -0.11,
                -0.09,
                -0.13,
                -0.07,
                -0.10,
            ],
            "coupling",
            config.reference_method,
            config.minimum_reference_size,
        ),
    }

    analysis = analyze_features(
        feature_values,
        references,
        config=config,
        source_dataset_id="TEST_MULTI_FEATURE",
        provenance={
            "source": "synthetic_test"
        },
    )

    results["multi_feature_analysis_created"] = (
        isinstance(
            analysis,
            AnomalyAnalysisResult,
        )
    )

    results["multi_feature_count_correct"] = (
        len(
            analysis.feature_results
        )
        == 3
    )

    results["aggregate_score_bounded"] = (
        analysis.aggregate_score is not None
        and 0.0
        <= analysis.aggregate_score
        <= 1.0
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    summary = (
        summarize_anomaly_analysis(
            analysis
        )
    )

    results["summary_created"] = (
        summary["feature_count"]
        == 3
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    valid, errors = (
        analysis.validate()
    )

    results["analysis_valid"] = (
        valid
    )

    # --------------------------------------------------------
    # Fingerprint
    # --------------------------------------------------------

    results["fingerprint_created"] = (
        len(
            analysis.fingerprint()
        )
        == 64
    )

    # --------------------------------------------------------
    # Missing value
    # --------------------------------------------------------

    missing_result = score_feature(
        None,
        reference,
        config=config,
    )

    results["missing_value_detected"] = (
        missing_result.quality
        == AnomalyQuality.MISSING
    )

    # --------------------------------------------------------
    # Non-finite value
    # --------------------------------------------------------

    nan_result = score_feature(
        float("nan"),
        reference,
        config=config,
    )

    results["nan_value_detected"] = (
        nan_result.quality
        == AnomalyQuality.NONFINITE
    )

    # --------------------------------------------------------
    # Insufficient reference
    # --------------------------------------------------------

    short_reference = (
        build_reference_statistics(
            [1.0, 1.1],
            "short_feature",
            config.reference_method,
            config.minimum_reference_size,
        )
    )

    short_result = score_feature(
        1.2,
        short_reference,
        config=config,
    )

    results["insufficient_reference_detected"] = (
        short_result.quality
        == AnomalyQuality.INSUFFICIENT_DATA
    )

    # --------------------------------------------------------
    # Payload validation
    # --------------------------------------------------------

    payload = {
        "feature_name": "entropy",
        "value": 2.5,
        "standardized_deviation": 3.2,
        "absolute_deviation": 1.1,
        "normalized_score": 1.0,
        "weight": 1.0,
        "level": AnomalyLevel.HIGH.value,
        "quality": AnomalyQuality.VALID.value,
    }

    payload_valid, payload_errors = (
        validate_anomaly_payload(
            payload
        )
    )

    results["payload_validation_passed"] = (
        payload_valid
    )

    # --------------------------------------------------------
    # Invalid payload
    # --------------------------------------------------------

    invalid_payload = {
        "feature_name": "entropy",
        "value": float("nan"),
        "normalized_score": 1.5,
        "weight": -1.0,
        "level": "PRIVATE_INTERNAL_STATE",
    }

    invalid_valid, invalid_errors = (
        validate_anomaly_payload(
            invalid_payload
        )
    )

    results["invalid_payload_rejected"] = (
        invalid_valid is False
    )

    # --------------------------------------------------------
    # Raw input preservation
    # --------------------------------------------------------

    original_values = [
        1.0,
        1.1,
        1.2,
        1.3,
        1.4,
    ]

    original_copy = list(
        original_values
    )

    _ = analyze_series_anomalies(
        original_values,
        feature_name="immutable_test",
        config=config,
    )

    results["raw_input_preserved"] = (
        original_values
        == original_copy
    )

    # --------------------------------------------------------
    # Security contract
    # --------------------------------------------------------

    contract = (
        anomaly_scoring_contract()
    )

    results["proprietary_code_absent"] = (
        contract[
            "proprietary_algorithms_included"
        ]
        is False
    )

    results["raw_modification_disabled"] = (
        contract[
            "raw_data_modification_allowed"
        ]
        is False
    )

    results["medical_diagnosis_disabled"] = (
        contract[
            "medical_diagnosis_supported"
        ]
        is False
    )

    results["flight_certification_disabled"] = (
        contract[
            "flight_certification_supported"
        ]
        is False
    )

    results["claim_class_is_c2"] = (
        contract[
            "claim_class"
        ]
        == "C2"
    )

    results["human_review_enforced"] = (
        contract[
            "human_review_required"
        ]
        is True
    )

    # --------------------------------------------------------
    # Final
    # --------------------------------------------------------

    boolean_checks = [
        value
        for value in results.values()
        if isinstance(value, bool)
    ]

    results["all_anomaly_checks_passed"] = (
        all(boolean_checks)
        if boolean_checks
        else False
    )

    return results


# ============================================================
# SELF TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 72)
    print(
        "D³ VITAL-X — Module 20: anomaly_scoring.py"
    )
    print("=" * 72)

    results = (
        run_anomaly_scoring_test()
    )

    for key, value in results.items():
        print(
            f"{key}: {value}"
        )

    print("=" * 72)

    if results[
        "all_anomaly_checks_passed"
    ]:

        print(
            "✅ ANOMALY SCORING MODULE TEST: PASS"
        )

    else:

        print(
            "❌ ANOMALY SCORING MODULE TEST: "
            "REVIEW REQUIRED"
        )

    print("=" * 72)
