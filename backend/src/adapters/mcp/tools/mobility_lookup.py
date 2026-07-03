from __future__ import annotations

import httpx
from langchain_core.tools import tool

from src.config import get_settings
from src.domain.exceptions.base import ExternalToolError

_PROMPT_TEMPLATE = (
    "Using live web search, summarize the CURRENT student/study-visa situation "
    "for a citizen of {country} seeking to study in {destination_country}. Cover: "
    "whether a student visa is required, any well-known restrictions, backlogs, "
    "or processing-time concerns, and how time-sensitive this information is. "
    "This is grounding for an admissions triage tool — be concrete, and "
    "explicitly note that visa policy changes, so this must be treated as a "
    "live, dated lookup, never a permanent fact."
)


async def lookup_student_mobility(country: str, destination_country: str) -> dict:
    """Live web-search-grounded lookup for student-visa/mobility considerations
    between two countries, via DashScope's native `enable_search` feature — no
    separate search-API key needed, rides on the existing Qwen Cloud key.

    Results must be presented as 'found via live lookup' and never asserted as
    a permanent fact from model memory (compatible-mode does not return
    structured citations, so the model is prompted to flag time-sensitivity
    inline instead).
    """
    settings = get_settings()
    if not settings.DASHSCOPE_API_KEY:
        raise ExternalToolError("DASHSCOPE_API_KEY is not configured")

    prompt = _PROMPT_TEMPLATE.format(country=country, destination_country=destination_country)

    async with httpx.AsyncClient(timeout=settings.DASHSCOPE_TIMEOUT) as client:
        resp = await client.post(
            f"{settings.DASHSCOPE_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.QWEN_MODEL_DEBATE,
                "messages": [{"role": "user", "content": prompt}],
                "enable_search": True,
                "search_options": {"forced_search": True},
                # Web search + thinking mode is unsupported for non-streaming
                # calls (DashScope 400s); we only need the grounded summary.
                "enable_thinking": False,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    summary = data["choices"][0]["message"]["content"]
    return {
        "country": country,
        "destination_country": destination_country,
        "summary": summary,
        "note": (
            "Live web-search-grounded lookup via Qwen — time-sensitive, "
            "verify before final decisions."
        ),
    }


@tool
async def mobility_lookup_tool(country: str, destination_country: str) -> dict:
    """Live, date-stamped lookup for student-visa/mobility considerations
    between the candidate's country and the professor's institution's country.
    Use when an international candidate's visa/mobility situation is plausibly
    a feasibility concern — never assume this from memory, always call this
    tool to get current, time-stamped information."""
    return await lookup_student_mobility(country, destination_country)
