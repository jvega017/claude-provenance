"""provenance.clean_room: Layer 6 clean-room generation (discipline mode).

The writer produces the draft from the writer pack only. SPEC §7
identifies two conformance levels:

- **Level 1 — discipline mode (this module)**: the writer entry point
  accepts ONLY a writer pack and a writer-model identifier. Additional
  context kwargs are refused at the API surface. This does not
  prevent a process-isolation breach inside the writer call itself,
  but it makes the breach a deliberate engineering choice rather than
  an accidental thread.
- **Level 2 — subprocess isolation**: the writer call happens in a
  subprocess with a scrubbed environment. Deferred. SPEC-L6-R001.

The discipline-mode wrapper does NOT itself call any LLM. It returns
an InvocationPlan describing what the writer would be called with.
The actual call is the caller's responsibility (their model client,
their API key, their cost).

This separation keeps the WarrantOS pipeline LLM-agnostic and
testable without network or credentials.

Stdlib only. Python 3.8 compatible.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from provenance.writer_pack import WriterPack


# Kwargs explicitly permitted on the writer invocation. Anything else
# raises at the API surface; this is the SPEC-L6-S001 discipline.
_PERMITTED_INVOCATION_KEYS = frozenset({
    "writer_pack",
    "writer_model",
    "writer_role",
    "max_tokens",
    "temperature",
})


@dataclass(frozen=True)
class InvocationPlan:
    """A plan describing how the writer SHOULD be invoked.

    The discipline mode produces this plan; the actual call is the
    caller's responsibility. The plan carries only the writer-pack
    contents plus the model identifier; no ledger rows, no process
    history, no tool traces.
    """

    writer_pack: Dict[str, Any]
    writer_model: str
    writer_role: str = "clean_room_writer"
    max_tokens: int = 4096
    temperature: float = 0.2

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "warrantos-invocation-plan/v1",
            "writer_pack": dict(self.writer_pack),
            "writer_model": self.writer_model,
            "writer_role": self.writer_role,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }


def prepare_invocation(
    writer_pack: WriterPack,
    writer_model: str,
    **kwargs: Any,
) -> InvocationPlan:
    """Build a discipline-mode invocation plan.

    SPEC-L6-S001 discipline: only the kwargs in `_PERMITTED_INVOCATION_KEYS`
    are accepted. Any other keyword raises ValueError. This blocks the
    common accidental thread where context history or feedback gets
    passed through as a "system prompt" or "context" kwarg that the
    writer then narrates back into final prose.

    Parameters
    ----------
    writer_pack
        The Layer 5 writer pack.
    writer_model
        The writer's model identifier (used by the Layer 7 G3
        self-grounding check to decide whether the grader is a
        different actor).
    **kwargs
        Optional overrides limited to `writer_role`, `max_tokens`,
        and `temperature`. Any other key raises.

    Returns
    -------
    InvocationPlan

    Raises
    ------
    ValueError
        If any kwarg is outside the permitted set, or if writer_model
        is empty.
    """
    if not writer_model or not writer_model.strip():
        raise ValueError("writer_model SHALL be a non-empty string")

    if not isinstance(writer_pack, WriterPack):
        raise TypeError(
            "writer_pack must be a WriterPack instance (got %r)"
            % type(writer_pack).__name__
        )

    rejected: List[str] = [k for k in kwargs if k not in _PERMITTED_INVOCATION_KEYS]
    if rejected:
        raise ValueError(
            "SPEC-L6-S001 discipline: refusing extra context kwargs: %s. "
            "Permitted keys: %s"
            % (sorted(rejected), sorted(_PERMITTED_INVOCATION_KEYS))
        )

    pack_dict = writer_pack.to_dict()

    plan = InvocationPlan(
        writer_pack=pack_dict,
        writer_model=writer_model.strip(),
        writer_role=str(kwargs.get("writer_role", "clean_room_writer")),
        max_tokens=int(kwargs.get("max_tokens", 4096)),
        temperature=float(kwargs.get("temperature", 0.2)),
    )
    return plan


def list_permitted_kwargs() -> List[str]:
    """Return the sorted list of kwargs the discipline mode accepts.

    Useful for callers building UI or documentation around the
    invocation surface.
    """
    return sorted(_PERMITTED_INVOCATION_KEYS)
