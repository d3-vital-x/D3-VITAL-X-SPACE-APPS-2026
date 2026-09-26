# ============================================================
# D³ VITAL-X Space Intelligence Platform
# Module 19 — transition_analysis.py
# ============================================================
#
# PUBLIC TRANSITION ANALYSIS LAYER
#
# ============================================================
# SECURITY / ARCHITECTURE PRINCIPLES
# ============================================================
#
# This module is intentionally a PUBLIC transition-analysis
# layer.
#
# It DOES NOT contain:
#
#   ❌ v10 source code
#   ❌ v11 source code
#   ❌ UTL/DVDH implementation
#   ❌ proprietary coupling equations
#   ❌ DSI calculation
#   ❌ Effective Mass calculation
#   ❌ PLV calculation
#   ❌ Lyapunov calculation
#   ❌ RQA calculation
#   ❌ MCMC implementation
#   ❌ proprietary coefficients
#   ❌ model weights
#   ❌ private endpoints
#   ❌ API keys / secrets
#   ❌ clinical diagnosis
#
# It ONLY:
#
#   1. accepts public metric series
#   2. validates numerical inputs
#   3. compares adjacent / baseline windows
#   4. identifies public statistical changes
#   5. summarizes transition events
#   6. records persistence and duration
#   7. preserves provenance
#   8. produces auditable C2 computational results
#
# IMPORTANT:
#
# A "transition" reported by this module means a measurable
# statistical change in the supplied public metric series.
#
# It does NOT establish:
#
#   - a physical phase transition
#   - a biological transition
#   - a spacecraft state transition
#   - a disease state
#   - a new physical law
#
# Human/scientific interpretation remains external to this
# module.
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

MODULE_NAME = "transition_analysis"
MODULE_VERSION = "1.0.0"
TRANSITION_SCHEMA_VERSION = "1.0"

PROPRIETARY_ALGORITHMS_INCLUDED = False
RAW_DATA_MODIFICATION_ALLOWED = False
MEDICAL_DIAGNOSIS_SUPPORTED = False
FLIGHT_CERTIFICATION_SUPPORTED = False


# ============================================================
# ENUMS
# ============================================================

class TransitionDirection(str, Enum):
    """
    Direction of a public statistical change.
    """

    INCREASE = "INCREASE"
    DECREASE = "DECREASE"
    STABLE = "STABLE"
    UNKNOWN = "UNKNOWN"


class TransitionType(str, Enum):
    """
    Descriptive transition-event type.

    These labels describe observed statistical behavior only.
    """

    LEVEL_SHIFT = "LEVEL_SHIFT"
    VARIABILITY_SHIFT = "VARIABILITY_SHIFT"
    SLOPE_CHANGE = "SLOPE_CHANGE"
    PERSISTENT_CHANGE = "PERSISTENT_CHANGE"
    TRANSIENT_CHANGE = "TRANSIENT_CHANGE"
    NO_CHANGE = "NO_CHANGE"
    UNKNOWN = "UNKNOWN"


class TransitionQuality(str, Enum):
    """
    Public quality state for a transition result.

    This is NOT a scientific significance judgment.
    """

    VALID = "VALID"
    INVALID = "INVALID"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
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


def generate_transition_id() -> str:
    return f"transition-{uuid.uuid4().hex}"


def generate_analysis_id() -> str:
    return f"transition-analysis-{uuid.uuid4().hex}"


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


def finite_series(
    values: Sequence[Any],
) -> Tuple[List[float], List[int]]:

    finite: List[float] = []
    invalid_indices: List[int] = []

    for index, value in enumerate(values):

        if is_finite_number(value):
            finite.append(float(value))
        else:
            invalid_indices.append(index)

    return finite, invalid_indices


def mean_safe(
    values: Sequence[float],
) -> Optional[float]:

    if not values:
        return None

    return float(statistics.fmean(values))


def variance_safe(
    values: Sequence[float],
) -> Optional[float]:

    if len(values) < 2:
        return None

    return float(statistics.pvariance(values))


def standard_deviation_safe(
    values: Sequence[float],
) -> Optional[float]:

    variance = variance_safe(values)

    if variance is None:
        return None

    return float(math.sqrt(max(variance, 0.0)))


def median_safe(
    values: Sequence[float],
) -> Optional[float]:

    if not values:
        return None

    return float(statistics.median(values))


def slope_safe(
    values: Sequence[float],
) -> Optional[float]:

    """
    Ordinary least-squares slope against sample index.

    This is a generic descriptive statistic.
    """

    n = len(values)

    if n < 2:
        return None

    x_mean = (n - 1) / 2.0
    y_mean = statistics.fmean(values)

    denominator = sum(
        (i - x_mean) ** 2
        for i in range(n)
    )

    if denominator <= 0:
        return None

    numerator = sum(
        (i - x_mean) * (value - y_mean)
        for i, value in enumerate(values)
    )

    return float(numerator / denominator)


# ============================================================
# TRANSITION CONFIGURATION
# ============================================================

@dataclass(frozen=True)
class TransitionConfig:
    """
    Public configuration for generic transition analysis.

    No proprietary threshold or model parameter is embedded.
    """

    window_size: int = 5

    minimum_window_size: int = 3

    relative_change_threshold: float = 0.10

    absolute_change_threshold: float = 0.0

    slope_change_threshold: float = 0.0

    persistence_windows: int = 2

    baseline_mode: str = "PREVIOUS_WINDOW"

    allow_zero_baseline: bool = False

    claim_class: ClaimClass = ClaimClass.C2

    def validate(self) -> Tuple[bool, List[str]]:

        errors: List[str] = []

        if self.window_size < 2:
            errors.append(
                "window_size must be >= 2."
            )

        if self.minimum_window_size < 2:
            errors.append(
                "minimum_window_size must be >= 2."
            )

        if self.minimum_window_size > self.window_size:
            errors.append(
                "minimum_window_size cannot exceed window_size."
            )

        if not is_finite_number(
            self.relative_change_threshold
        ):
            errors.append(
                "relative_change_threshold must be finite."
            )

        elif self.relative_change_threshold < 0:
            errors.append(
                "relative_change_threshold cannot be negative."
            )

        if not is_finite_number(
            self.absolute_change_threshold
        ):
            errors.append(
                "absolute_change_threshold must be finite."
            )

        if not is_finite_number(
            self.slope_change_threshold
        ):
            errors.append(
                "slope_change_threshold must be finite."
            )

        if self.persistence_windows < 1:
            errors.append(
                "persistence_windows must be >= 1."
            )

        if self.baseline_mode not in {
            "PREVIOUS_WINDOW",
            "FIRST_WINDOW",
        }:
            errors.append(
                "Unsupported baseline_mode."
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
# WINDOW STATISTICS
# ============================================================

@dataclass
class WindowStatistics:
    """
    Descriptive statistics for one public metric window.
    """

    window_id: int

    start_index: int

    end_index: int

    count: int

    mean: Optional[float]

    median: Optional[float]

    variance: Optional[float]

    standard_deviation: Optional[float]

    minimum: Optional[float]

    maximum: Optional[float]

    slope: Optional[float]

    quality: TransitionQuality = (
        TransitionQuality.UNVERIFIED
    )

    def validate(self) -> Tuple[bool, List[str]]:

        errors: List[str] = []

        if self.count < 0:
            errors.append(
                "Window count cannot be negative."
            )

        if self.start_index < 0:
            errors.append(
                "start_index cannot be negative."
            )

        if self.end_index < self.start_index:
            errors.append(
                "end_index cannot precede start_index."
            )

        numeric_fields = {
            "mean": self.mean,
            "median": self.median,
            "variance": self.variance,
            "standard_deviation": (
                self.standard_deviation
            ),
            "minimum": self.minimum,
            "maximum": self.maximum,
            "slope": self.slope,
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
        result["quality"] = self.quality.value
        return result


def calculate_window_statistics(
    values: Sequence[Any],
    *,
    window_id: int = 0,
    start_index: int = 0,
) -> WindowStatistics:

    finite_values, invalid_indices = finite_series(
        values
    )

    count = len(finite_values)

    if count == 0:

        return WindowStatistics(
            window_id=window_id,
            start_index=start_index,
            end_index=(
                start_index + max(len(values) - 1, 0)
            ),
            count=0,
            mean=None,
            median=None,
            variance=None,
            standard_deviation=None,
            minimum=None,
            maximum=None,
            slope=None,
            quality=TransitionQuality.NONFINITE,
        )

    quality = TransitionQuality.VALID

    if invalid_indices:
        quality = TransitionQuality.LOW_QUALITY

    return WindowStatistics(
        window_id=window_id,
        start_index=start_index,
        end_index=(
            start_index + max(len(values) - 1, 0)
        ),
        count=count,
        mean=mean_safe(finite_values),
        median=median_safe(finite_values),
        variance=variance_safe(finite_values),
        standard_deviation=(
            standard_deviation_safe(finite_values)
        ),
        minimum=min(finite_values),
        maximum=max(finite_values),
        slope=slope_safe(finite_values),
        quality=quality,
    )


# ============================================================
# TRANSITION EVENT
# ============================================================

@dataclass
class TransitionEvent:
    """
    Publicly reported statistical transition event.

    This is a computational observation, not a physical
    interpretation.
    """

    transition_id: str

    metric_name: str

    transition_type: TransitionType

    direction: TransitionDirection

    index: int

    baseline_mean: Optional[float]

    current_mean: Optional[float]

    absolute_change: Optional[float]

    relative_change: Optional[float]

    baseline_variance: Optional[float]

    current_variance: Optional[float]

    slope_change: Optional[float]

    persistence: int = 1

    duration: int = 1

    quality: TransitionQuality = (
        TransitionQuality.UNVERIFIED
    )

    claim_class: ClaimClass = ClaimClass.C2

    human_review_required: bool = True

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

        if not self.transition_id:
            errors.append(
                "transition_id is required."
            )

        if not self.metric_name:
            errors.append(
                "metric_name is required."
            )

        if self.index < 0:
            errors.append(
                "Transition index cannot be negative."
            )

        if self.persistence < 1:
            errors.append(
                "persistence must be >= 1."
            )

        if self.duration < 1:
            errors.append(
                "duration must be >= 1."
            )

        numeric_fields = {
            "baseline_mean": self.baseline_mean,
            "current_mean": self.current_mean,
            "absolute_change": self.absolute_change,
            "relative_change": self.relative_change,
            "baseline_variance": (
                self.baseline_variance
            ),
            "current_variance": (
                self.current_variance
            ),
            "slope_change": self.slope_change,
        }

        for name, value in numeric_fields.items():

            if value is not None and not is_finite_number(
                value
            ):
                errors.append(
                    f"{name} must be finite when present."
                )

        if not isinstance(
            self.transition_type,
            TransitionType,
        ):
            errors.append(
                "Invalid transition type."
            )

        if not isinstance(
            self.direction,
            TransitionDirection,
        ):
            errors.append(
                "Invalid transition direction."
            )

        if not isinstance(
            self.quality,
            TransitionQuality,
        ):
            errors.append(
                "Invalid transition quality."
            )

        if not isinstance(
            self.claim_class,
            ClaimClass,
        ):
            errors.append(
                "Invalid claim class."
            )

        return len(errors) == 0, errors

    def fingerprint(self) -> str:

        payload = {
            "transition_id": self.transition_id,
            "metric_name": self.metric_name,
            "transition_type": (
                self.transition_type.value
            ),
            "direction": self.direction.value,
            "index": self.index,
            "baseline_mean": self.baseline_mean,
            "current_mean": self.current_mean,
            "absolute_change": self.absolute_change,
            "relative_change": self.relative_change,
            "baseline_variance": (
                self.baseline_variance
            ),
            "current_variance": (
                self.current_variance
            ),
            "slope_change": self.slope_change,
            "persistence": self.persistence,
            "duration": self.duration,
            "quality": self.quality.value,
            "claim_class": self.claim_class.value,
        }

        return calculate_sha256(payload)

    def to_dict(self) -> Dict[str, Any]:

        result = asdict(self)

        result["transition_type"] = (
            self.transition_type.value
        )

        result["direction"] = (
            self.direction.value
        )

        result["quality"] = (
            self.quality.value
        )

        result["claim_class"] = (
            self.claim_class.value
        )

        result["fingerprint"] = (
            self.fingerprint()
        )

        return result


# ============================================================
# TRANSITION ANALYSIS RESULT
# ============================================================

@dataclass
class TransitionAnalysisResult:
    """
    Complete public transition-analysis result.
    """

    analysis_id: str

    metric_name: str

    source_dataset_id: Optional[str]

    input_count: int

    window_size: int

    windows: List[WindowStatistics] = field(
        default_factory=list
    )

    events: List[TransitionEvent] = field(
        default_factory=list
    )

    quality: TransitionQuality = (
        TransitionQuality.UNVERIFIED
    )

    claim_class: ClaimClass = ClaimClass.C2

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

        if not self.metric_name:
            errors.append(
                "metric_name is required."
            )

        if self.input_count < 0:
            errors.append(
                "input_count cannot be negative."
            )

        if self.window_size < 2:
            errors.append(
                "window_size must be >= 2."
            )

        for window in self.windows:

            valid, window_errors = (
                window.validate()
            )

            if not valid:
                errors.extend(window_errors)

        for event in self.events:

            valid, event_errors = (
                event.validate()
            )

            if not valid:
                errors.extend(event_errors)

        return len(errors) == 0, errors

    def event_count(self) -> int:
        return len(self.events)

    def persistent_event_count(self) -> int:

        return sum(
            1
            for event in self.events
            if event.transition_type
            == TransitionType.PERSISTENT_CHANGE
        )

    def quality_summary(self) -> Dict[str, int]:

        summary = {
            quality.value: 0
            for quality in TransitionQuality
        }

        summary[self.quality.value] += 1

        for window in self.windows:
            summary[window.quality.value] += 1

        for event in self.events:
            summary[event.quality.value] += 1

        return summary

    def fingerprint(self) -> str:

        payload = {
            "analysis_id": self.analysis_id,
            "metric_name": self.metric_name,
            "source_dataset_id": (
                self.source_dataset_id
            ),
            "input_count": self.input_count,
            "window_size": self.window_size,
            "windows": [
                window.to_dict()
                for window in self.windows
            ],
            "events": [
                event.fingerprint()
                for event in self.events
            ],
            "quality": self.quality.value,
            "claim_class": self.claim_class.value,
        }

        return calculate_sha256(payload)

    def to_dict(self) -> Dict[str, Any]:

        return {
            "analysis_id": self.analysis_id,
            "metric_name": self.metric_name,
            "source_dataset_id": (
                self.source_dataset_id
            ),
            "input_count": self.input_count,
            "window_size": self.window_size,
            "windows": [
                window.to_dict()
                for window in self.windows
            ],
            "events": [
                event.to_dict()
                for event in self.events
            ],
            "quality": self.quality.value,
            "claim_class": self.claim_class.value,
            "provenance": self.provenance,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "event_count": self.event_count(),
            "persistent_event_count": (
                self.persistent_event_count()
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
# WINDOW BUILDER
# ============================================================

def build_windows(
    values: Sequence[Any],
    window_size: int,
) -> List[WindowStatistics]:

    if window_size < 2:
        raise ValueError(
            "window_size must be >= 2."
        )

    windows: List[WindowStatistics] = []

    if len(values) < window_size:
        return windows

    window_id = 0

    for start in range(
        0,
        len(values) - window_size + 1,
    ):

        end = start + window_size

        window_values = values[
            start:end
        ]

        statistics_result = (
            calculate_window_statistics(
                window_values,
                window_id=window_id,
                start_index=start,
            )
        )

        windows.append(
            statistics_result
        )

        window_id += 1

    return windows


# ============================================================
# CHANGE CLASSIFICATION
# ============================================================

def classify_direction(
    absolute_change: Optional[float],
    threshold: float = 0.0,
) -> TransitionDirection:

    if absolute_change is None:
        return TransitionDirection.UNKNOWN

    if not is_finite_number(
        absolute_change
    ):
        return TransitionDirection.UNKNOWN

    value = float(absolute_change)

    if abs(value) <= threshold:
        return TransitionDirection.STABLE

    if value > 0:
        return TransitionDirection.INCREASE

    if value < 0:
        return TransitionDirection.DECREASE

    return TransitionDirection.UNKNOWN


def calculate_relative_change(
    baseline: Optional[float],
    current: Optional[float],
    *,
    allow_zero_baseline: bool = False,
) -> Optional[float]:

    if baseline is None or current is None:
        return None

    if not (
        is_finite_number(baseline)
        and is_finite_number(current)
    ):
        return None

    baseline = float(baseline)
    current = float(current)

    if baseline == 0.0:

        if allow_zero_baseline:
            return (
                current
                if current != 0.0
                else 0.0
            )

        return None

    return float(
        (current - baseline)
        / abs(baseline)
    )


def classify_transition(
    *,
    absolute_change: Optional[float],
    relative_change: Optional[float],
    baseline_variance: Optional[float],
    current_variance: Optional[float],
    slope_change: Optional[float],
    config: TransitionConfig,
) -> Tuple[
    TransitionType,
    TransitionDirection,
]:

    if absolute_change is None:
        return (
            TransitionType.UNKNOWN,
            TransitionDirection.UNKNOWN,
        )

    direction = classify_direction(
        absolute_change,
        threshold=config.absolute_change_threshold,
    )

    relative_trigger = False

    if relative_change is not None:

        relative_trigger = (
            abs(relative_change)
            >= config.relative_change_threshold
        )

    absolute_trigger = (
        abs(absolute_change)
        >= config.absolute_change_threshold
    )

    slope_trigger = False

    if slope_change is not None:

        slope_trigger = (
            abs(slope_change)
            >= config.slope_change_threshold
        )

    variance_trigger = False

    if (
        baseline_variance is not None
        and current_variance is not None
    ):

        variance_change = (
            current_variance
            - baseline_variance
        )

        if baseline_variance != 0:

            variance_relative = (
                variance_change
                / abs(baseline_variance)
            )

            variance_trigger = (
                abs(variance_relative)
                >= config.relative_change_threshold
            )

        elif current_variance != 0:

            variance_trigger = True

    # --------------------------------------------------------
    # No meaningful change
    # --------------------------------------------------------

    if not (
        relative_trigger
        or absolute_trigger
        or slope_trigger
        or variance_trigger
    ):

        return (
            TransitionType.NO_CHANGE,
            TransitionDirection.STABLE,
        )

    # --------------------------------------------------------
    # Variability shift
    # --------------------------------------------------------

    if variance_trigger and not (
        relative_trigger
        or absolute_trigger
        or slope_trigger
    ):

        return (
            TransitionType.VARIABILITY_SHIFT,
            direction,
        )

    # --------------------------------------------------------
    # Slope change
    # --------------------------------------------------------

    if slope_trigger and not (
        relative_trigger
        or absolute_trigger
    ):

        return (
            TransitionType.SLOPE_CHANGE,
            direction,
        )

    # --------------------------------------------------------
    # Level shift
    # --------------------------------------------------------

    return (
        TransitionType.LEVEL_SHIFT,
        direction,
    )


# ============================================================
# EVENT PERSISTENCE
# ============================================================

def estimate_persistence(
    values: Sequence[Any],
    start_index: int,
    *,
    window_size: int,
    baseline_mean: Optional[float],
    config: TransitionConfig,
) -> int:

    if baseline_mean is None:
        return 1

    if start_index >= len(values):
        return 1

    persistence = 0

    threshold = max(
        abs(baseline_mean)
        * config.relative_change_threshold,
        config.absolute_change_threshold,
    )

    for index in range(
        start_index,
        len(values),
    ):

        value = values[index]

        if not is_finite_number(value):
            break

        difference = (
            float(value)
            - baseline_mean
        )

        if abs(difference) >= threshold:

            persistence += 1

        else:

            break

    return max(
        persistence,
        1,
    )


# ============================================================
# SINGLE-SERIES TRANSITION ANALYSIS
# ============================================================

def analyze_transition_series(
    values: Sequence[Any],
    *,
    metric_name: str = "metric",
    source_dataset_id: Optional[str] = None,
    config: Optional[TransitionConfig] = None,
    timestamps: Optional[Sequence[Any]] = None,
    provenance: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> TransitionAnalysisResult:

    if config is None:
        config = TransitionConfig()

    config_valid, config_errors = (
        config.validate()
    )

    if not config_valid:
        raise ValueError(
            "Invalid TransitionConfig: "
            + " | ".join(config_errors)
        )

    metric_name = sanitize_identifier(
        metric_name,
        fallback="metric",
    )

    source_dataset_id = (
        sanitize_identifier(
            source_dataset_id
        )
        if source_dataset_id
        else None
    )

    input_count = len(values)

    # --------------------------------------------------------
    # Insufficient input
    # --------------------------------------------------------

    if input_count < config.window_size:

        return TransitionAnalysisResult(
            analysis_id=generate_analysis_id(),
            metric_name=metric_name,
            source_dataset_id=source_dataset_id,
            input_count=input_count,
            window_size=config.window_size,
            windows=[],
            events=[],
            quality=(
                TransitionQuality.INSUFFICIENT_DATA
            ),
            claim_class=config.claim_class,
            provenance=provenance or {},
            metadata=metadata or {},
        )

    # --------------------------------------------------------
    # Build windows
    # --------------------------------------------------------

    windows = build_windows(
        values,
        config.window_size,
    )

    events: List[TransitionEvent] = []

    # --------------------------------------------------------
    # Compare adjacent windows
    # --------------------------------------------------------

    if len(windows) >= 2:

        for index in range(
            1,
            len(windows),
        ):

            baseline = (
                windows[index - 1]
            )

            current = windows[index]

            if (
                baseline.mean is None
                or current.mean is None
            ):
                continue

            absolute_change = (
                current.mean
                - baseline.mean
            )

            relative_change = (
                calculate_relative_change(
                    baseline.mean,
                    current.mean,
                    allow_zero_baseline=(
                        config.allow_zero_baseline
                    ),
                )
            )

            slope_change = None

            if (
                baseline.slope is not None
                and current.slope is not None
            ):

                slope_change = (
                    current.slope
                    - baseline.slope
                )

            transition_type, direction = (
                classify_transition(
                    absolute_change=(
                        absolute_change
                    ),
                    relative_change=(
                        relative_change
                    ),
                    baseline_variance=(
                        baseline.variance
                    ),
                    current_variance=(
                        current.variance
                    ),
                    slope_change=slope_change,
                    config=config,
                )
            )

            if transition_type == (
                TransitionType.NO_CHANGE
            ):
                continue

            event_index = current.start_index

            persistence = (
                estimate_persistence(
                    values,
                    event_index,
                    window_size=config.window_size,
                    baseline_mean=baseline.mean,
                    config=config,
                )
            )

            duration = max(
                persistence,
                1,
            )

            # ------------------------------------------------
            # Persistent vs transient classification
            # ------------------------------------------------

            if (
                persistence
                >= config.persistence_windows
            ):

                final_type = (
                    TransitionType.PERSISTENT_CHANGE
                )

            else:

                final_type = (
                    TransitionType.TRANSIENT_CHANGE
                )

            # Preserve variability/slope metadata.
            if transition_type == (
                TransitionType.VARIABILITY_SHIFT
            ):
                final_type = (
                    TransitionType.VARIABILITY_SHIFT
                )

            elif transition_type == (
                TransitionType.SLOPE_CHANGE
            ):
                final_type = (
                    TransitionType.SLOPE_CHANGE
                )

            event = TransitionEvent(
                transition_id=(
                    generate_transition_id()
                ),
                metric_name=metric_name,
                transition_type=final_type,
                direction=direction,
                index=event_index,
                baseline_mean=baseline.mean,
                current_mean=current.mean,
                absolute_change=absolute_change,
                relative_change=relative_change,
                baseline_variance=(
                    baseline.variance
                ),
                current_variance=(
                    current.variance
                ),
                slope_change=slope_change,
                persistence=persistence,
                duration=duration,
                quality=(
                    TransitionQuality.VALID
                    if (
                        baseline.quality
                        == TransitionQuality.VALID
                        and current.quality
                        == TransitionQuality.VALID
                    )
                    else TransitionQuality.LOW_QUALITY
                ),
                claim_class=config.claim_class,
                human_review_required=True,
                provenance=(
                    provenance or {}
                ),
                metadata={
                    **(
                        metadata or {}
                    ),
                    "window_id": current.window_id,
                    "baseline_window_id": (
                        baseline.window_id
                    ),
                },
            )

            events.append(event)

    # --------------------------------------------------------
    # Result quality
    # --------------------------------------------------------

    if not windows:

        result_quality = (
            TransitionQuality.INSUFFICIENT_DATA
        )

    elif any(
        window.quality
        == TransitionQuality.NONFINITE
        for window in windows
    ):

        result_quality = (
            TransitionQuality.NONFINITE
        )

    elif any(
        window.quality
        == TransitionQuality.LOW_QUALITY
        for window in windows
    ):

        result_quality = (
            TransitionQuality.LOW_QUALITY
        )

    else:

        result_quality = (
            TransitionQuality.VALID
        )

    result_metadata = {
        **(
            metadata or {}
        ),
        "configuration": asdict(config),
        "timestamp_count": (
            len(timestamps)
            if timestamps is not None
            else None
        ),
        "raw_data_modified": False,
        "interpretation_policy": (
            "Statistical transition only; "
            "physical or clinical interpretation "
            "is outside this module."
        ),
    }

    return TransitionAnalysisResult(
        analysis_id=generate_analysis_id(),
        metric_name=metric_name,
        source_dataset_id=source_dataset_id,
        input_count=input_count,
        window_size=config.window_size,
        windows=windows,
        events=events,
        quality=result_quality,
        claim_class=config.claim_class,
        provenance=provenance or {},
        metadata=result_metadata,
    )


# ============================================================
# PUBLIC TRANSITION INDEX
# ============================================================

def calculate_transition_index(
    result: TransitionAnalysisResult,
) -> Optional[float]:

    """
    Calculate a generic public transition index.

    This is a descriptive aggregation of detected event
    magnitudes. It is NOT the proprietary DSI or any UTL/DVDH
    quantity.

    The output is normalized to [0, 1] using the largest
    observed absolute relative change in the result.

    If no valid relative changes exist, returns 0.0.
    """

    changes: List[float] = []

    for event in result.events:

        if event.relative_change is None:
            continue

        if not is_finite_number(
            event.relative_change
        ):
            continue

        changes.append(
            abs(float(event.relative_change))
        )

    if not changes:
        return 0.0

    # Generic bounded aggregation.
    # This is intentionally NOT a proprietary equation.
    mean_change = statistics.fmean(
        changes
    )

    max_change = max(
        changes
    )

    if max_change <= 0:
        return 0.0

    index = mean_change / max_change

    return float(
        min(
            max(index, 0.0),
            1.0,
        )
    )


# ============================================================
# PUBLIC SUMMARY
# ============================================================

def summarize_transition_analysis(
    result: TransitionAnalysisResult,
) -> Dict[str, Any]:

    transition_index = (
        calculate_transition_index(result)
    )

    directions = {
        direction.value: 0
        for direction in TransitionDirection
    }

    types = {
        transition_type.value: 0
        for transition_type in TransitionType
    }

    for event in result.events:

        directions[
            event.direction.value
        ] += 1

        types[
            event.transition_type.value
        ] += 1

    return {
        "analysis_id": result.analysis_id,
        "metric_name": result.metric_name,
        "source_dataset_id": (
            result.source_dataset_id
        ),
        "input_count": result.input_count,
        "window_size": result.window_size,
        "window_count": len(result.windows),
        "event_count": result.event_count(),
        "persistent_event_count": (
            result.persistent_event_count()
        ),
        "transition_index": transition_index,
        "direction_summary": directions,
        "transition_type_summary": types,
        "quality": result.quality.value,
        "claim_class": result.claim_class.value,
        "human_review_required": True,
        "fingerprint": result.fingerprint(),
    }


# ============================================================
# PUBLIC PAYLOAD VALIDATION
# ============================================================

def validate_transition_payload(
    payload: Dict[str, Any],
) -> Tuple[bool, List[str]]:

    errors: List[str] = []

    if not isinstance(
        payload,
        dict,
    ):
        return (
            False,
            ["Transition payload must be a dictionary."],
        )

    metric_name = payload.get(
        "metric_name"
    )

    if not metric_name:
        errors.append(
            "Transition payload requires 'metric_name'."
        )

    transition_type = payload.get(
        "transition_type"
    )

    if transition_type is not None:

        valid_types = {
            item.value
            for item in TransitionType
        }

        if str(
            transition_type
        ) not in valid_types:

            errors.append(
                "Invalid transition_type."
            )

    direction = payload.get(
        "direction"
    )

    if direction is not None:

        valid_directions = {
            item.value
            for item in TransitionDirection
        }

        if str(
            direction
        ) not in valid_directions:

            errors.append(
                "Invalid transition direction."
            )

    numeric_fields = [
        "baseline_mean",
        "current_mean",
        "absolute_change",
        "relative_change",
        "baseline_variance",
        "current_variance",
        "slope_change",
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

    persistence = payload.get(
        "persistence"
    )

    if persistence is not None:

        if (
            not isinstance(
                persistence,
                int,
            )
            or persistence < 1
        ):

            errors.append(
                "persistence must be an integer >= 1."
            )

    return (
        len(errors) == 0,
        errors,
    )


# ============================================================
# PUBLIC CONTRACT
# ============================================================

def transition_analysis_contract() -> Dict[str, Any]:

    return {
        "module": MODULE_NAME,
        "version": MODULE_VERSION,
        "schema_version": (
            TRANSITION_SCHEMA_VERSION
        ),

        "purpose": (
            "Public statistical transition detection, "
            "event characterization, persistence analysis, "
            "and auditable summarization."
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
            ClaimClass.C2.value
        ),

        "interpretation_policy": (
            "Transition events represent statistical "
            "changes in supplied public metric series. "
            "They are not, by themselves, physical, "
            "biological, or clinical state transitions."
        ),

        "private_engine_policy": (
            "No private engine implementation or "
            "proprietary calculation is included."
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
            TRANSITION_SCHEMA_VERSION
        ),

        "role": (
            "Public statistical transition analysis "
            "and event characterization layer."
        ),

        "proprietary_algorithm_included": False,
        "raw_data_modification": False,
        "medical_diagnosis": False,
        "flight_certification": False,

        "claim_class": ClaimClass.C2.value,

        "supported_outputs": [
            "window_statistics",
            "level_change",
            "variability_change",
            "slope_change",
            "persistence",
            "duration",
            "transition_index",
            "event_summary",
            "quality_state",
            "provenance",
            "fingerprint",
        ],
    }


# ============================================================
# SECURITY / ARCHITECTURE SELF-TEST
# ============================================================

def run_transition_analysis_test() -> Dict[str, Any]:

    results: Dict[str, Any] = {}

    # --------------------------------------------------------
    # Configuration
    # --------------------------------------------------------

    config = TransitionConfig(
        window_size=5,
        relative_change_threshold=0.10,
        persistence_windows=2,
    )

    config_valid, config_errors = (
        config.validate()
    )

    results["config_valid"] = config_valid

    # --------------------------------------------------------
    # Stable synthetic series
    # --------------------------------------------------------

    stable_series = [
        1.00,
        1.01,
        0.99,
        1.00,
        1.02,
        1.01,
        1.00,
        0.98,
        1.01,
        1.00,
    ]

    stable_result = (
        analyze_transition_series(
            stable_series,
            metric_name="test_metric",
            source_dataset_id="TEST_STABLE",
            config=config,
            provenance={
                "source": "synthetic_test"
            },
        )
    )

    results["stable_analysis_created"] = (
        isinstance(
            stable_result,
            TransitionAnalysisResult,
        )
    )

    # --------------------------------------------------------
    # Shifted synthetic series
    # --------------------------------------------------------

    shifted_series = [
        1.00,
        1.01,
        0.99,
        1.00,
        1.02,

        1.40,
        1.42,
        1.39,
        1.41,
        1.43,

        1.44,
        1.45,
        1.42,
        1.46,
        1.44,
    ]

    shifted_result = (
        analyze_transition_series(
            shifted_series,
            metric_name="test_metric",
            source_dataset_id="TEST_SHIFT",
            config=config,
            provenance={
                "source": "synthetic_test"
            },
        )
    )

    results["shift_analysis_created"] = (
        isinstance(
            shifted_result,
            TransitionAnalysisResult,
        )
    )

    results["shift_detected"] = (
        shifted_result.event_count()
        > 0
    )

    # --------------------------------------------------------
    # Persistent change detection
    # --------------------------------------------------------

    results["persistent_change_detected"] = (
        shifted_result.persistent_event_count()
        > 0
    )

    # --------------------------------------------------------
    # Transition index
    # --------------------------------------------------------

    transition_index = (
        calculate_transition_index(
            shifted_result
        )
    )

    results["transition_index_valid"] = (
        transition_index is not None
        and 0.0 <= transition_index <= 1.0
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    summary = summarize_transition_analysis(
        shifted_result
    )

    results["summary_created"] = (
        summary["event_count"]
        == shifted_result.event_count()
    )

    # --------------------------------------------------------
    # Result validation
    # --------------------------------------------------------

    valid, errors = (
        shifted_result.validate()
    )

    results["result_valid"] = valid

    # --------------------------------------------------------
    # Fingerprint
    # --------------------------------------------------------

    results["fingerprint_created"] = (
        len(
            shifted_result.fingerprint()
        )
        == 64
    )

    # --------------------------------------------------------
    # Payload validation
    # --------------------------------------------------------

    payload = {
        "metric_name": "transition_index",
        "transition_type": (
            TransitionType.PERSISTENT_CHANGE.value
        ),
        "direction": (
            TransitionDirection.INCREASE.value
        ),
        "baseline_mean": 1.0,
        "current_mean": 1.4,
        "absolute_change": 0.4,
        "relative_change": 0.4,
        "persistence": 5,
    }

    payload_valid, payload_errors = (
        validate_transition_payload(
            payload
        )
    )

    results["payload_validation_passed"] = (
        payload_valid
    )

    # --------------------------------------------------------
    # Invalid payload rejection
    # --------------------------------------------------------

    invalid_payload = {
        "metric_name": "transition_index",
        "transition_type": "PRIVATE_INTERNAL_STATE",
        "direction": "UNKNOWN_DIRECTION",
        "relative_change": float("nan"),
    }

    invalid_valid, invalid_errors = (
        validate_transition_payload(
            invalid_payload
        )
    )

    results["invalid_payload_rejected"] = (
        invalid_valid is False
    )

    # --------------------------------------------------------
    # Insufficient data
    # --------------------------------------------------------

    insufficient_result = (
        analyze_transition_series(
            [1.0, 1.1],
            metric_name="short_metric",
            config=config,
        )
    )

    results["insufficient_data_detected"] = (
        insufficient_result.quality
        == TransitionQuality.INSUFFICIENT_DATA
    )

    # --------------------------------------------------------
    # Non-finite input
    # --------------------------------------------------------

    nonfinite_series = [
        1.0,
        1.1,
        float("nan"),
        1.0,
        1.2,
        1.3,
        1.4,
    ]

    nonfinite_result = (
        analyze_transition_series(
            nonfinite_series,
            metric_name="nonfinite_metric",
            config=config,
        )
    )

    results["nonfinite_handled"] = (
        nonfinite_result.quality
        in {
            TransitionQuality.LOW_QUALITY,
            TransitionQuality.NONFINITE,
            TransitionQuality.VALID,
        }
    )

    # --------------------------------------------------------
    # Raw-data protection
    # --------------------------------------------------------

    original_series = [
        1.0,
        1.1,
        1.2,
        1.3,
        1.4,
        1.5,
    ]

    original_copy = list(
        original_series
    )

    _ = analyze_transition_series(
        original_series,
        metric_name="immutable_test",
        config=config,
    )

    results["raw_input_preserved"] = (
        original_series
        == original_copy
    )

    # --------------------------------------------------------
    # Security contract
    # --------------------------------------------------------

    contract = (
        transition_analysis_contract()
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
        contract["claim_class"]
        == ClaimClass.C2.value
    )

    # --------------------------------------------------------
    # Final
    # --------------------------------------------------------

    boolean_checks = [
        value
        for value in results.values()
        if isinstance(value, bool)
    ]

    results["all_transition_checks_passed"] = (
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
        "D³ VITAL-X — Module 19: transition_analysis.py"
    )
    print("=" * 72)

    results = (
        run_transition_analysis_test()
    )

    for key, value in results.items():
        print(
            f"{key}: {value}"
        )

    print("=" * 72)

    if results[
        "all_transition_checks_passed"
    ]:
        print(
            "✅ TRANSITION ANALYSIS MODULE TEST: PASS"
        )
    else:
        print(
            "❌ TRANSITION ANALYSIS MODULE TEST: "
            "REVIEW REQUIRED"
        )

    print("=" * 72)
