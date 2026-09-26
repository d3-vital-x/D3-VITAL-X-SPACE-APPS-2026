# ============================================================
# 22. explainability.py
# D³ VITAL-X Space Intelligence Platform
#
# Public Explainability & Evidence Layer
#
# PURPOSE
# -------
# Convert public computational outputs into transparent,
# human-readable evidence summaries.
#
# IMPORTANT
# ---------
# - No proprietary D³/UTL algorithm
# - No v10/v11 source
# - No hidden physics interpretation
# - No medical diagnosis
# - No spacecraft flight certification
# - No raw-data modification
# - No autonomous decision authority
#
# Explainability means:
#   "What public evidence contributed to this output?"
#
# It does NOT mean:
#   "What is the physical cause of this phenomenon?"
# ============================================================

from __future__ import annotations

import json
import math
import hashlib

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
)


# ============================================================
# MODULE METADATA
# ============================================================

MODULE_NAME = "explainability"
MODULE_VERSION = "1.0.0"
EXPLAINABILITY_SCHEMA_VERSION = "1.0"

PROPRIETARY_ALGORITHMS_INCLUDED = False
RAW_DATA_MODIFICATION_ALLOWED = False
MEDICAL_DIAGNOSIS_SUPPORTED = False
FLIGHT_CERTIFICATION_SUPPORTED = False
AUTONOMOUS_DECISION_SUPPORTED = False


# ============================================================
# ENUMS
# ============================================================

class EvidenceDirection(str, Enum):
    """
    Describes how an evidence item relates to an output.

    IMPORTANT:
    These are computational/reporting directions, not
    causal physical interpretations.
    """

    SUPPORTING = "supporting"
    CONTRADICTING = "contradicting"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


class EvidenceStrength(str, Enum):
    """
    Descriptive evidence-strength labels.

    These are NOT statistical significance levels.
    """

    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"
    UNKNOWN = "unknown"


class ExplanationLevel(str, Enum):
    """
    Output detail level.
    """

    BRIEF = "brief"
    STANDARD = "standard"
    DETAILED = "detailed"


class ReviewStatus(str, Enum):
    """
    Human-review state.
    """

    NOT_REQUIRED = "not_required"
    RECOMMENDED = "recommended"
    REQUIRED = "required"


class ClaimClass(str, Enum):
    """
    Public claim classification.

    C1 = directly measured/reported
    C2 = computationally derived
    C3 = hypothesis/future interpretation
    """

    C1 = "C1"
    C2 = "C2"
    C3 = "C3"


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
    Deterministic SHA-256 hash.
    """

    payload = canonical_json(value).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


def is_finite_number(value: Any) -> bool:
    """
    Return True when value is a finite number.
    """

    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def clamp(
    value: float,
    lower: float = 0.0,
    upper: float = 1.0,
) -> float:
    """
    Clamp value to a bounded interval.
    """

    return max(
        lower,
        min(upper, float(value)),
    )


def safe_float(
    value: Any,
) -> Optional[float]:
    """
    Convert finite numeric values to float.
    """

    if not is_finite_number(value):
        return None

    return float(value)


def sanitize_text(
    value: Any,
    max_length: int = 500,
) -> str:
    """
    Convert arbitrary text into bounded display text.
    """

    text = str(value).strip()

    if len(text) > max_length:
        text = text[:max_length] + "..."

    return text


# ============================================================
# EVIDENCE STRENGTH
# ============================================================

def evidence_strength_from_score(
    score: Optional[float],
) -> EvidenceStrength:
    """
    Convert normalized evidence score into a descriptive label.

    These thresholds are presentation conventions only.
    """

    if score is None:
        return EvidenceStrength.UNKNOWN

    if not is_finite_number(score):
        return EvidenceStrength.UNKNOWN

    value = clamp(float(score))

    if value < 0.20:
        return EvidenceStrength.VERY_LOW

    if value < 0.40:
        return EvidenceStrength.LOW

    if value < 0.60:
        return EvidenceStrength.MODERATE

    if value < 0.80:
        return EvidenceStrength.HIGH

    return EvidenceStrength.VERY_HIGH


# ============================================================
# EVIDENCE ITEM
# ============================================================

@dataclass
class EvidenceItem:
    """
    One transparent evidence contribution.

    This object records:
      - what was observed/computed
      - what baseline/reference was used
      - how strongly it contributed
      - whether it supported or contradicted an output

    It does NOT infer physical causation.
    """

    metric_name: str

    observed_value: Optional[float] = None

    reference_value: Optional[float] = None

    deviation: Optional[float] = None

    contribution: Optional[float] = None

    weight: Optional[float] = None

    direction: EvidenceDirection = (
        EvidenceDirection.UNKNOWN
    )

    strength: EvidenceStrength = (
        EvidenceStrength.UNKNOWN
    )

    unit: Optional[str] = None

    quality: Optional[float] = None

    uncertainty: Optional[float] = None

    claim_class: ClaimClass = ClaimClass.C2

    source: str = "public_metric"

    note: str = ""

    provenance: Dict[str, Any] = field(
        default_factory=dict
    )

    created_at: str = field(
        default_factory=utc_timestamp
    )

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate evidence item.
        """

        errors: List[str] = []

        if not self.metric_name:
            errors.append(
                "metric_name cannot be empty."
            )

        for field_name, value in [
            ("observed_value", self.observed_value),
            ("reference_value", self.reference_value),
            ("deviation", self.deviation),
            ("contribution", self.contribution),
            ("weight", self.weight),
            ("quality", self.quality),
            ("uncertainty", self.uncertainty),
        ]:

            if value is not None:

                if not is_finite_number(value):
                    errors.append(
                        f"{field_name} must be finite."
                    )

        if self.quality is not None:

            if not 0.0 <= float(self.quality) <= 1.0:
                errors.append(
                    "quality must be between 0 and 1."
                )

        if self.weight is not None:

            if float(self.weight) < 0:
                errors.append(
                    "weight cannot be negative."
                )

        if self.uncertainty is not None:

            if float(self.uncertainty) < 0:
                errors.append(
                    "uncertainty cannot be negative."
                )

        return len(errors) == 0, errors

    def fingerprint(self) -> str:
        """
        Stable evidence fingerprint.
        """

        return calculate_sha256(
            {
                "metric_name": self.metric_name,
                "observed_value": self.observed_value,
                "reference_value": self.reference_value,
                "deviation": self.deviation,
                "contribution": self.contribution,
                "weight": self.weight,
                "direction": self.direction.value,
                "strength": self.strength.value,
                "unit": self.unit,
                "quality": self.quality,
                "uncertainty": self.uncertainty,
                "claim_class": self.claim_class.value,
                "source": self.source,
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize evidence item.
        """

        payload = asdict(self)

        payload["direction"] = self.direction.value
        payload["strength"] = self.strength.value
        payload["claim_class"] = self.claim_class.value

        payload["fingerprint"] = self.fingerprint()

        return payload


# ============================================================
# EVIDENCE CONSTRUCTOR
# ============================================================

def create_evidence(
    metric_name: str,
    observed_value: Optional[float] = None,
    reference_value: Optional[float] = None,
    deviation: Optional[float] = None,
    contribution: Optional[float] = None,
    weight: Optional[float] = None,
    direction: EvidenceDirection = (
        EvidenceDirection.UNKNOWN
    ),
    quality: Optional[float] = None,
    uncertainty: Optional[float] = None,
    unit: Optional[str] = None,
    claim_class: ClaimClass = ClaimClass.C2,
    source: str = "public_metric",
    note: str = "",
    provenance: Optional[Dict[str, Any]] = None,
) -> EvidenceItem:
    """
    Create and validate a public evidence item.
    """

    item = EvidenceItem(
        metric_name=sanitize_text(
            metric_name,
            max_length=200,
        ),
        observed_value=(
            None
            if observed_value is None
            else float(observed_value)
        ),
        reference_value=(
            None
            if reference_value is None
            else float(reference_value)
        ),
        deviation=(
            None
            if deviation is None
            else float(deviation)
        ),
        contribution=(
            None
            if contribution is None
            else float(contribution)
        ),
        weight=(
            None
            if weight is None
            else float(weight)
        ),
        direction=direction,
        strength=evidence_strength_from_score(
            None
            if contribution is None
            else abs(float(contribution))
        ),
        quality=(
            None
            if quality is None
            else float(quality)
        ),
        uncertainty=(
            None
            if uncertainty is None
            else float(uncertainty)
        ),
        unit=unit,
        claim_class=claim_class,
        source=source,
        note=sanitize_text(
            note,
            max_length=500,
        ),
        provenance=provenance or {},
    )

    valid, errors = item.validate()

    if not valid:
        raise ValueError(
            "Invalid evidence item: "
            + "; ".join(errors)
        )

    return item


# ============================================================
# EXPLANATION RESULT
# ============================================================

@dataclass
class ExplanationResult:
    """
    Human-readable explanation of a computational result.
    """

    output_name: str

    output_value: Optional[float] = None

    output_label: str = ""

    summary: str = ""

    evidence: List[EvidenceItem] = field(
        default_factory=list
    )

    evidence_count: int = 0

    supporting_count: int = 0

    contradicting_count: int = 0

    neutral_count: int = 0

    evidence_coverage: float = 0.0

    confidence: Optional[float] = None

    review_status: ReviewStatus = (
        ReviewStatus.RECOMMENDED
    )

    claim_class: ClaimClass = ClaimClass.C2

    limitations: List[str] = field(
        default_factory=list
    )

    provenance: Dict[str, Any] = field(
        default_factory=dict
    )

    created_at: str = field(
        default_factory=utc_timestamp
    )

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate explanation.
        """

        errors: List[str] = []

        if not self.output_name:
            errors.append(
                "output_name cannot be empty."
            )

        if self.output_value is not None:

            if not is_finite_number(
                self.output_value
            ):
                errors.append(
                    "output_value must be finite."
                )

        if not 0.0 <= float(
            self.evidence_coverage
        ) <= 1.0:
            errors.append(
                "evidence_coverage must be between 0 and 1."
            )

        if self.confidence is not None:

            if not 0.0 <= float(
                self.confidence
            ) <= 1.0:
                errors.append(
                    "confidence must be between 0 and 1."
                )

        for item in self.evidence:

            valid, item_errors = item.validate()

            if not valid:
                errors.extend(item_errors)

        return len(errors) == 0, errors

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize complete explanation.
        """

        return {
            "output_name": self.output_name,
            "output_value": self.output_value,
            "output_label": self.output_label,
            "summary": self.summary,

            "evidence": [
                item.to_dict()
                for item in self.evidence
            ],

            "evidence_count": self.evidence_count,
            "supporting_count": self.supporting_count,
            "contradicting_count": self.contradicting_count,
            "neutral_count": self.neutral_count,

            "evidence_coverage": (
                self.evidence_coverage
            ),

            "confidence": self.confidence,

            "review_status": (
                self.review_status.value
            ),

            "claim_class": (
                self.claim_class.value
            ),

            "limitations": self.limitations,

            "provenance": self.provenance,

            "created_at": self.created_at,
        }

    def to_json(
        self,
        indent: int = 2,
    ) -> str:
        """
        JSON representation.
        """

        return json.dumps(
            self.to_dict(),
            indent=indent,
            ensure_ascii=False,
            default=str,
        )

    def fingerprint(self) -> str:
        """
        Stable fingerprint of explanation.
        """

        return calculate_sha256(
            self.to_dict()
        )


# ============================================================
# EXPLANATION ENGINE
# ============================================================

def build_explanation(
    output_name: str,
    output_value: Optional[float],
    evidence: Sequence[EvidenceItem],
    output_label: str = "",
    confidence: Optional[float] = None,
    review_status: ReviewStatus = (
        ReviewStatus.RECOMMENDED
    ),
    claim_class: ClaimClass = ClaimClass.C2,
    limitations: Optional[
        Sequence[str]
    ] = None,
    provenance: Optional[
        Dict[str, Any]
    ] = None,
) -> ExplanationResult:
    """
    Build transparent explanation from public evidence.

    No physical interpretation is inferred.
    """

    evidence_list = list(evidence)

    supporting = sum(
        1
        for item in evidence_list
        if item.direction
        == EvidenceDirection.SUPPORTING
    )

    contradicting = sum(
        1
        for item in evidence_list
        if item.direction
        == EvidenceDirection.CONTRADICTING
    )

    neutral = sum(
        1
        for item in evidence_list
        if item.direction
        == EvidenceDirection.NEUTRAL
    )

    coverage = (
        min(
            1.0,
            len(evidence_list) / 5.0,
        )
        if evidence_list
        else 0.0
    )

    if evidence_list:

        names = [
            item.metric_name
            for item in evidence_list
        ]

        summary = (
            f"{output_name} was derived from "
            f"{len(evidence_list)} public evidence item(s): "
            + ", ".join(names)
            + "."
        )

    else:

        summary = (
            f"No public evidence items were available "
            f"to explain {output_name}."
        )

    result = ExplanationResult(
        output_name=output_name,
        output_value=output_value,
        output_label=output_label,
        summary=summary,
        evidence=evidence_list,
        evidence_count=len(evidence_list),
        supporting_count=supporting,
        contradicting_count=contradicting,
        neutral_count=neutral,
        evidence_coverage=coverage,
        confidence=(
            None
            if confidence is None
            else clamp(float(confidence))
        ),
        review_status=review_status,
        claim_class=claim_class,
        limitations=list(
            limitations or []
        ),
        provenance=provenance or {},
    )

    valid, errors = result.validate()

    if not valid:
        raise ValueError(
            "Invalid explanation: "
            + "; ".join(errors)
        )

    return result


# ============================================================
# TEXT EXPLANATION
# ============================================================

def explain_as_text(
    explanation: ExplanationResult,
    level: ExplanationLevel = (
        ExplanationLevel.STANDARD
    ),
) -> str:
    """
    Convert ExplanationResult into reviewer-friendly text.
    """

    lines: List[str] = []

    lines.append(
        f"Output: {explanation.output_name}"
    )

    if explanation.output_label:
        lines.append(
            f"Label: {explanation.output_label}"
        )

    if explanation.output_value is not None:

        lines.append(
            f"Value: {explanation.output_value:.6g}"
        )

    lines.append(
        f"Evidence items: "
        f"{explanation.evidence_count}"
    )

    if explanation.confidence is not None:

        lines.append(
            f"Confidence indicator: "
            f"{explanation.confidence:.3f}"
        )

    lines.append(
        f"Review status: "
        f"{explanation.review_status.value}"
    )

    if level in (
        ExplanationLevel.STANDARD,
        ExplanationLevel.DETAILED,
    ):

        lines.append("")
        lines.append(
            "Why this result was produced:"
        )

        if explanation.evidence:

            for item in explanation.evidence:

                direction = (
                    item.direction.value
                )

                contribution = (
                    "n/a"
                    if item.contribution is None
                    else f"{item.contribution:.4f}"
                )

                lines.append(
                    f"- {item.metric_name}: "
                    f"direction={direction}, "
                    f"contribution={contribution}"
                )

                if (
                    level
                    == ExplanationLevel.DETAILED
                    and item.note
                ):

                    lines.append(
                        f"  note: {item.note}"
                    )

        else:

            lines.append(
                "- No evidence was available."
            )

    if level == ExplanationLevel.DETAILED:

        lines.append("")
        lines.append(
            "Limitations:"
        )

        if explanation.limitations:

            for limitation in (
                explanation.limitations
            ):

                lines.append(
                    f"- {limitation}"
                )

        else:

            lines.append(
                "- No additional limitations supplied."
            )

    return "\n".join(lines)


# ============================================================
# CONTRIBUTION RANKING
# ============================================================

def rank_evidence(
    evidence: Sequence[EvidenceItem],
    descending: bool = True,
) -> List[EvidenceItem]:
    """
    Rank evidence by absolute contribution.

    This is an evidence-ordering operation only.
    It is NOT a ranking of scientific importance.
    """

    return sorted(
        list(evidence),
        key=lambda item: (
            abs(
                float(item.contribution)
            )
            if item.contribution is not None
            else 0.0
        ),
        reverse=descending,
    )


# ============================================================
# PUBLIC METRIC EXPLANATION HELPER
# ============================================================

def explain_metric_contribution(
    metric_name: str,
    observed_value: float,
    reference_value: Optional[float] = None,
    contribution: Optional[float] = None,
    direction: EvidenceDirection = (
        EvidenceDirection.UNKNOWN
    ),
    quality: Optional[float] = None,
    uncertainty: Optional[float] = None,
    unit: Optional[str] = None,
    note: str = "",
) -> EvidenceItem:
    """
    Convenience helper for public metrics.

    No causal interpretation is added.
    """

    deviation = None

    if (
        reference_value is not None
        and is_finite_number(observed_value)
        and is_finite_number(reference_value)
    ):

        deviation = (
            float(observed_value)
            - float(reference_value)
        )

    return create_evidence(
        metric_name=metric_name,
        observed_value=observed_value,
        reference_value=reference_value,
        deviation=deviation,
        contribution=contribution,
        direction=direction,
        quality=quality,
        uncertainty=uncertainty,
        unit=unit,
        claim_class=ClaimClass.C2,
        source="public_metric",
        note=note,
    )


# ============================================================
# SAFETY / REVIEW HELPERS
# ============================================================

def add_default_limitations(
    explanation: ExplanationResult,
) -> ExplanationResult:
    """
    Add standard reviewer-safe limitations.
    """

    defaults = [
        "Explanation describes computational evidence only.",
        "Evidence contribution does not establish physical causation.",
        "Results should be interpreted together with uncertainty and data quality.",
        "Anomaly indicators are not medical diagnoses.",
        "Anomaly indicators are not spacecraft safety certification.",
        "Human review remains required for consequential interpretation.",
    ]

    existing = list(
        explanation.limitations
    )

    for item in defaults:

        if item not in existing:
            existing.append(item)

    explanation.limitations = existing

    return explanation


def requires_human_review(
    explanation: ExplanationResult,
) -> bool:
    """
    Return whether human review is required/recommended.
    """

    return explanation.review_status in (
        ReviewStatus.RECOMMENDED,
        ReviewStatus.REQUIRED,
    )


# ============================================================
# PUBLIC EXPLAINABILITY CONTRACT
# ============================================================

def explainability_contract() -> Dict[str, Any]:
    """
    Machine-readable public contract.
    """

    return {
        "module_name": MODULE_NAME,
        "module_version": MODULE_VERSION,
        "schema_version":
            EXPLAINABILITY_SCHEMA_VERSION,

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

        "purpose": (
            "Transparent reporting of public "
            "computational evidence."
        ),

        "limitations": [
            "Does not establish physical causality.",
            "Does not diagnose disease.",
            "Does not certify spacecraft safety.",
            "Does not expose proprietary algorithms.",
            "Does not modify raw input data.",
            "Does not replace human scientific review.",
        ],
    }


# ============================================================
# VALIDATION
# ============================================================

def validate_explanation_payload(
    payload: Any,
) -> Tuple[bool, List[str]]:
    """
    Validate ExplanationResult or dictionary payload.
    """

    if isinstance(
        payload,
        ExplanationResult,
    ):
        return payload.validate()

    if not isinstance(payload, dict):

        return False, [
            "Payload must be ExplanationResult or dict."
        ]

    errors: List[str] = []

    if not payload.get("output_name"):

        errors.append(
            "output_name is required."
        )

    if "evidence_coverage" in payload:

        coverage = payload[
            "evidence_coverage"
        ]

        if not is_finite_number(coverage):

            errors.append(
                "evidence_coverage must be finite."
            )

        elif not 0.0 <= float(coverage) <= 1.0:

            errors.append(
                "evidence_coverage must be between 0 and 1."
            )

    if "confidence" in payload:

        confidence = payload[
            "confidence"
        ]

        if confidence is not None:

            if not is_finite_number(
                confidence
            ):

                errors.append(
                    "confidence must be finite."
                )

            elif not 0.0 <= float(
                confidence
            ) <= 1.0:

                errors.append(
                    "confidence must be between 0 and 1."
                )

    return len(errors) == 0, errors


# ============================================================
# SELF TEST
# ============================================================

def run_explainability_test() -> Dict[str, Any]:
    """
    Internal validation suite.
    """

    results: Dict[str, Any] = {}

    # --------------------------------------------------------
    # Test 1: Evidence creation
    # --------------------------------------------------------

    e1 = explain_metric_contribution(
        metric_name="entropy",
        observed_value=1.20,
        reference_value=1.00,
        contribution=0.60,
        direction=EvidenceDirection.SUPPORTING,
        quality=0.90,
        uncertainty=0.05,
        unit="bits",
        note="Synthetic entropy deviation.",
    )

    results["evidence_creation"] = (
        e1.validate()[0]
    )

    # --------------------------------------------------------
    # Test 2: Second evidence item
    # --------------------------------------------------------

    e2 = explain_metric_contribution(
        metric_name="variance",
        observed_value=1.80,
        reference_value=2.00,
        contribution=-0.30,
        direction=EvidenceDirection.CONTRADICTING,
        quality=0.85,
        uncertainty=0.10,
        unit="unit²",
        note="Synthetic variance deviation.",
    )

    results["second_evidence_creation"] = (
        e2.validate()[0]
    )

    # --------------------------------------------------------
    # Test 3: Explanation
    # --------------------------------------------------------

    explanation = build_explanation(
        output_name="anomaly_score",
        output_value=0.42,
        output_label="Research Review Indicator",
        evidence=[e1, e2],
        confidence=0.82,
        review_status=ReviewStatus.REQUIRED,
        claim_class=ClaimClass.C2,
    )

    results["explanation_creation"] = (
        explanation.validate()[0]
    )

    # --------------------------------------------------------
    # Test 4: Evidence counts
    # --------------------------------------------------------

    results["evidence_count"] = (
        explanation.evidence_count == 2
    )

    results["supporting_count"] = (
        explanation.supporting_count == 1
    )

    results["contradicting_count"] = (
        explanation.contradicting_count == 1
    )

    # --------------------------------------------------------
    # Test 5: Coverage
    # --------------------------------------------------------

    results["coverage_test"] = (
        0.0 <= explanation.evidence_coverage <= 1.0
    )

    # --------------------------------------------------------
    # Test 6: Text explanation
    # --------------------------------------------------------

    text = explain_as_text(
        explanation,
        level=ExplanationLevel.DETAILED,
    )

    results["text_explanation_test"] = (
        isinstance(text, str)
        and "anomaly_score" in text
        and "entropy" in text
        and "variance" in text
    )

    # --------------------------------------------------------
    # Test 7: Evidence ranking
    # --------------------------------------------------------

    ranked = rank_evidence(
        [e1, e2]
    )

    results["ranking_test"] = (
        len(ranked) == 2
        and ranked[0].metric_name == "entropy"
    )

    # --------------------------------------------------------
    # Test 8: Limitations
    # --------------------------------------------------------

    add_default_limitations(
        explanation
    )

    results["limitations_test"] = (
        len(explanation.limitations) >= 5
    )

    # --------------------------------------------------------
    # Test 9: Human review
    # --------------------------------------------------------

    results["human_review_test"] = (
        requires_human_review(
            explanation
        )
        is True
    )

    # --------------------------------------------------------
    # Test 10: Serialization
    # --------------------------------------------------------

    payload = explanation.to_dict()

    results["serialization_test"] = (
        isinstance(payload, dict)
        and payload["output_name"]
        == "anomaly_score"
        and len(payload["evidence"]) == 2
    )

    # --------------------------------------------------------
    # Test 11: JSON
    # --------------------------------------------------------

    json_text = explanation.to_json()

    results["json_test"] = (
        isinstance(json_text, str)
        and len(json_text) > 0
        and '"output_name"' in json_text
    )

    # --------------------------------------------------------
    # Test 12: Fingerprint
    # --------------------------------------------------------

    fingerprint = explanation.fingerprint()

    results["fingerprint_test"] = (
        isinstance(fingerprint, str)
        and len(fingerprint) == 64
    )

    # --------------------------------------------------------
    # Test 13: No proprietary algorithm
    # --------------------------------------------------------

    results["proprietary_disabled"] = (
        PROPRIETARY_ALGORITHMS_INCLUDED
        is False
    )

    # --------------------------------------------------------
    # Test 14: Raw modification disabled
    # --------------------------------------------------------

    results["raw_modification_disabled"] = (
        RAW_DATA_MODIFICATION_ALLOWED
        is False
    )

    # --------------------------------------------------------
    # Test 15: Medical diagnosis disabled
    # --------------------------------------------------------

    results["medical_diagnosis_disabled"] = (
        MEDICAL_DIAGNOSIS_SUPPORTED
        is False
    )

    # --------------------------------------------------------
    # Test 16: Flight certification disabled
    # --------------------------------------------------------

    results["flight_certification_disabled"] = (
        FLIGHT_CERTIFICATION_SUPPORTED
        is False
    )

    # --------------------------------------------------------
    # Test 17: Autonomous decision disabled
    # --------------------------------------------------------

    results["autonomous_decision_disabled"] = (
        AUTONOMOUS_DECISION_SUPPORTED
        is False
    )

    # --------------------------------------------------------
    # FINAL
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
    Return module metadata.
    """

    return {
        "module": MODULE_NAME,
        "version": MODULE_VERSION,
        "schema_version":
            EXPLAINABILITY_SCHEMA_VERSION,

        "purpose": (
            "Transparent explanation of public "
            "computational evidence."
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

        "autonomous_decision_supported":
            AUTONOMOUS_DECISION_SUPPORTED,

        "claim_class": ClaimClass.C2.value,

        "contract":
            explainability_contract(),
    }


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    print("=" * 64)
    print("D³ VITAL-X | explainability.py")
    print("=" * 64)

    results = run_explainability_test()

    for key, value in results.items():

        status = "✅" if value else "❌"

        print(
            f"{status} {key}: {value}"
        )

    print("-" * 64)

    if results["all_tests_passed"]:

        print(
            "🚀 ALL EXPLAINABILITY TESTS PASSED"
        )

    else:

        print(
            "❌ SOME EXPLAINABILITY TESTS FAILED"
        )

    print("=" * 64)
