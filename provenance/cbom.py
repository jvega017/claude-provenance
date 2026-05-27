"""Context Bill of Materials helpers for WarrantOS review packs.

The CBOM records what context entered an artefact, how it was transformed,
which material was admitted or blocked, which claims rely on it, and which
review findings remain attached to the artefact.

Stdlib only. Python 3.8 compatible.
"""

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


@dataclass(frozen=True)
class ContextInput:
    """A context item considered for use in an artefact."""

    context_id: str
    text: str
    source: str = ""
    material_type: str = "context"
    admitted: bool = True
    reason: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "context_id": self.context_id,
            "text": self.text,
            "source": self.source,
            "material_type": self.material_type,
            "admitted": self.admitted,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class TransformationRecord:
    """A transformation from one or more context inputs to an output."""

    transform_id: str
    input_ids: List[str]
    output_id: str
    kind: str
    description: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "transform_id": self.transform_id,
            "input_ids": list(self.input_ids),
            "output_id": self.output_id,
            "kind": self.kind,
            "description": self.description,
        }


@dataclass(frozen=True)
class ClaimRecord:
    """A claim carried by the artefact and its supporting material."""

    claim_id: str
    text: str
    support_ids: List[str] = field(default_factory=list)
    status: str = "unreviewed"

    def to_dict(self) -> Dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "support_ids": list(self.support_ids),
            "status": self.status,
        }


@dataclass(frozen=True)
class ReviewFindingRecord:
    """A review finding attached to the CBOM."""

    finding_id: str
    severity: str
    title: str
    disposition: str = "distinct"

    def to_dict(self) -> Dict[str, object]:
        return {
            "finding_id": self.finding_id,
            "severity": self.severity,
            "title": self.title,
            "disposition": self.disposition,
        }


@dataclass(frozen=True)
class CBOM:
    """A serialisable WarrantOS Context Bill of Materials."""

    artefact_id: str
    context_inputs: List[ContextInput]
    transformations: List[TransformationRecord]
    claims: List[ClaimRecord]
    review_findings: List[ReviewFindingRecord]
    schema: str = "warrantos-cbom/v1"

    def to_dict(self) -> Dict[str, object]:
        admitted = [item for item in self.context_inputs if item.admitted]
        blocked = [item for item in self.context_inputs if not item.admitted]
        return {
            "schema": self.schema,
            "artefact_id": self.artefact_id,
            "summary": {
                "context_inputs": len(self.context_inputs),
                "admitted_material": len(admitted),
                "blocked_material": len(blocked),
                "transformations": len(self.transformations),
                "claims": len(self.claims),
                "review_findings": len(self.review_findings),
            },
            "context_inputs": [item.to_dict() for item in self.context_inputs],
            "admitted_material": [item.to_dict() for item in admitted],
            "blocked_material": [item.to_dict() for item in blocked],
            "transformations": [item.to_dict() for item in self.transformations],
            "claims": [item.to_dict() for item in self.claims],
            "review_findings": [item.to_dict() for item in self.review_findings],
        }


def build_cbom(
    context_inputs: Optional[Iterable[ContextInput]] = None,
    transformations: Optional[Iterable[TransformationRecord]] = None,
    claims: Optional[Iterable[ClaimRecord]] = None,
    review_findings: Optional[Iterable[ReviewFindingRecord]] = None,
    artefact_id: str = "",
) -> CBOM:
    """Build and validate a CBOM."""
    input_list = list(context_inputs or [])
    transform_list = list(transformations or [])
    claim_list = list(claims or [])
    finding_list = list(review_findings or [])

    _validate_references(input_list, transform_list, claim_list)
    return CBOM(
        artefact_id=artefact_id,
        context_inputs=input_list,
        transformations=transform_list,
        claims=claim_list,
        review_findings=finding_list,
    )


def _validate_references(
    context_inputs: List[ContextInput],
    transformations: List[TransformationRecord],
    claims: List[ClaimRecord],
) -> None:
    known_ids = {item.context_id for item in context_inputs}
    admitted_ids = {item.context_id for item in context_inputs if item.admitted}

    for transform in transformations:
        missing = [input_id for input_id in transform.input_ids if input_id not in known_ids]
        if missing:
            raise ValueError(
                "transformation %s references unknown context input(s): %s"
                % (transform.transform_id, ", ".join(missing))
            )

    for claim in claims:
        missing = [support_id for support_id in claim.support_ids if support_id not in known_ids]
        if missing:
            raise ValueError(
                "claim %s references unknown support input(s): %s"
                % (claim.claim_id, ", ".join(missing))
            )
        blocked = [support_id for support_id in claim.support_ids if support_id not in admitted_ids]
        if blocked:
            raise ValueError(
                "claim %s references blocked support input(s): %s"
                % (claim.claim_id, ", ".join(blocked))
            )
