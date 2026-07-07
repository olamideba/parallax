from __future__ import annotations

from src.adapters.qwen_cloud.chat_model import get_chat_model
from src.adapters.qwen_cloud.templates import render_prompt
from src.application.ports.outbound.gatekeeper import Gatekeeper, GatekeeperAssessment
from src.domain.models.society import AgentRole


class QwenGatekeeper(Gatekeeper):
    """Gatekeeper triage backed by the cheap Qwen model via structured output."""

    async def assess(
        self,
        *,
        sender_email: str,
        subject: str | None,
        body: str,
        cv_text: str | None,
        professor_topics: list[str],
        custom_instructions: str | None,
        aggressiveness: float,
    ) -> GatekeeperAssessment:
        prompt = render_prompt(
            "gatekeeper.j2",
            sender_email=sender_email,
            subject=subject,
            body=body,
            cv_text=cv_text,
            professor_topics=professor_topics,
            custom_instructions=custom_instructions,
            aggressiveness=aggressiveness,
        )
        model = get_chat_model(AgentRole.GATEKEEPER).with_structured_output(
            GatekeeperAssessment
        )
        result = await model.ainvoke(prompt)
        return result if isinstance(result, GatekeeperAssessment) else GatekeeperAssessment(
            **dict(result)
        )
