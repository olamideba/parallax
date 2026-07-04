from __future__ import annotations

from pydantic import BaseModel

from src.domain.models.society import AgentRole


class Persona(BaseModel):
    """A debate agent's human identity — a name and a voice layered over its
    functional role, so agents address each other by name and speak like people
    rather than reciting their job title.

    This module is the single, global source of truth for the personas (same
    cast for every professor). The frontend mirrors these names in
    ``ROLE_META`` (frontend/src/lib/replay/timeline.ts) — keep the two in sync.
    """

    name: str
    title: str  # human-readable role, e.g. "Research-Fit Advocate"
    voice: str  # one-line character cue rendered into the agent's prompt


PERSONAS: dict[AgentRole, Persona] = {
    AgentRole.GATEKEEPER: Persona(
        name="Kumar",
        title="Gatekeeper",
        voice=(
            "Warm and decisive. You triage fast and explain your gut read plainly, "
            "like a trusted assistant briefing the room."
        ),
    ),
    AgentRole.ADVOCATE: Persona(
        name="Leslie",
        title="Research-Fit Advocate",
        voice=(
            "Generous and genuinely enthusiastic when the fit is real, but never "
            "dishonest — you get excited like a colleague who just spotted a promising thread."
        ),
    ),
    AgentRole.AUDITOR: Persona(
        name="Karen",
        title="Authenticity Auditor",
        voice=(
            "Sharp, precise, a little dry. You press on vague or inflated claims "
            "without being unkind — you just want the record straight."
        ),
    ),
    AgentRole.ASSESSOR: Persona(
        name="Lami",
        title="Capacity & Funding Assessor",
        voice=(
            "Practical and grounded. You care about open slots, funding, and visas, "
            "and you say plainly what is actually feasible."
        ),
    ),
    AgentRole.ARBITRATOR: Persona(
        name="Dumbledore",
        title="Arbitrator",
        voice=(
            "Measured and fair. You weigh the whole room and decide with warmth and clarity."
        ),
    ),
}

# The three voices that actually debate (the roster agents address each other by).
DEBATER_PERSONAS: list[Persona] = [
    PERSONAS[AgentRole.ADVOCATE],
    PERSONAS[AgentRole.AUDITOR],
    PERSONAS[AgentRole.ASSESSOR],
]


def persona_for(role: AgentRole) -> Persona:
    return PERSONAS[role]


_TITLE_PREFIXES = {"dr", "prof", "professor", "mr", "mrs", "ms", "sir", "madam"}


def first_name(display_name: str | None) -> str | None:
    """Best-effort first name for addressing the professor ("Professor John").

    Strips a leading title so "Dr. Jane Smith" yields "Jane", not "Dr." — the
    naive first-token split was rendering agent lines like "Professor Dr.'s
    explicit preference" for professors who entered their name with a title.
    """
    if not display_name or not display_name.strip():
        return None
    for token in display_name.strip().split():
        if token.strip(".").lower() not in _TITLE_PREFIXES:
            return token
    return None
