from __future__ import annotations

import re

from langchain_core.messages import HumanMessage

from src.adapters.qwen_cloud.chat_model import get_chat_model
from src.adapters.qwen_cloud.personas import persona_for
from src.application.ports.outbound.spoken_line_writer import SpokenLineWriter
from src.config import get_settings
from src.domain.models.society import AgentRole

# The evidentiary text is written to be *read* — [REF:n] chips, formal citations,
# several audited claims packed into one turn. Spoken, that runs minutes long and
# sounds like a document. This collapses it to one short spoken beat in the
# agent's own voice, dropping citation syntax and keeping only the point.
_PROMPT = """You rewrite a written debate turn as a single short spoken line for {name} \
({title}) to say aloud. {name}'s manner: {voice}

Rules:
- One or two sentences, at most {max_words} words. Conversational, contractions okay.
- Speak the point, not the paperwork. Drop [REF:n] / [RECEIPT:...] markers and formal \
citations; if a source matters, mention it as an aside ("I checked her transformer paper").
- If the turn audits several claims, lead with the single strongest one.
- No stage directions, no quotes around it, no preamble. Output only the spoken line.

Written turn:
{content}"""

# Strip evidence markup defensively in case the model leaves any in.
_REF_MARKER = re.compile(r"\[(?:REF|RECEIPT)[^\]]*\]", re.IGNORECASE)


class QwenSpokenLineWriter(SpokenLineWriter):
    """Compresses a turn's `content` to a spoken line via the same Qwen chat path
    as the debate (routes through DashScope, satisfies the Qwen-Cloud-only rule)."""

    async def to_spoken_line(self, role: AgentRole, content: str) -> str:
        persona = persona_for(role)
        max_words = get_settings().DEBATE_SPOKEN_LINE_MAX_WORDS
        prompt = _PROMPT.format(
            name=persona.name,
            title=persona.title,
            voice=persona.voice,
            max_words=max_words,
            content=content,
        )
        model = get_chat_model(role)
        response = await model.ainvoke([HumanMessage(content=prompt)])
        line = _REF_MARKER.sub("", str(response.content)).strip().strip('"')
        return line
