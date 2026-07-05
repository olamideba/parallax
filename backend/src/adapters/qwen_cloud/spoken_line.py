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
({title}) to say aloud in a live admissions panel. {name}'s manner: {voice}

The panel is discussing a candidate ({professor_ref} is the professor whose lab and \
published work the candidate is being weighed against).

Rules:
- One or two sentences, at most {max_words} words. Conversational, contractions okay.
- Speak the point, not the paperwork. Drop any [REF:n] / [RECEIPT:...] markers and formal \
citations; say the substance plainly.
- Ground it strictly in the written turn below. Do NOT invent specifics — no paper titles, \
methods, or numbers that aren't already in the text.
- Keep two things straight and never blur them: the CANDIDATE's own claims/submitted \
evidence versus {professor_ref}'s published corpus and lab needs. When the point is that \
evidence is missing, it's the candidate's evidence that's missing, not the professor's.
- Refer to the professor as {professor_ref} or use singular "they/their". Never guess a \
gender or use "he/she/his/her" for the professor.
- Vary how you speak: don't open with the same word or phrase every turn, and don't start \
by naming the person you're answering every single time. Avoid the crutch "I checked ..." — \
say what you found, not that you checked.
- If the turn covers several claims, lead with the single strongest one.
- No stage directions, no quotes around it, no preamble. Output only the spoken line.

Written turn:
{content}"""

# Strip evidence markup defensively in case the model leaves any in.
_REF_MARKER = re.compile(r"\[(?:REF|RECEIPT)[^\]]*\]", re.IGNORECASE)


class QwenSpokenLineWriter(SpokenLineWriter):
    """Compresses a turn's `content` to a spoken line via the same Qwen chat path
    as the debate (routes through DashScope, satisfies the Qwen-Cloud-only rule)."""

    async def to_spoken_line(
        self, role: AgentRole, content: str, professor_name: str | None = None
    ) -> str:
        persona = persona_for(role)
        max_words = get_settings().DEBATE_SPOKEN_LINE_MAX_WORDS
        professor_ref = (
            professor_name.strip()
            if professor_name and professor_name.strip()
            else "the professor"
        )
        prompt = _PROMPT.format(
            name=persona.name,
            title=persona.title,
            voice=persona.voice,
            professor_ref=professor_ref,
            max_words=max_words,
            content=content,
        )
        model = get_chat_model(role)
        response = await model.ainvoke([HumanMessage(content=prompt)])
        line = _REF_MARKER.sub("", str(response.content)).strip().strip('"')
        return line
