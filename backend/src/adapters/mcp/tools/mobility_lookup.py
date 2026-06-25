from __future__ import annotations


async def lookup_student_mobility(country: str, destination_country: str) -> dict:
    """Live, date-stamped lookup for visa/mobility restrictions.

    Results must be presented as 'found via live lookup, dated X, source Y'
    and never asserted as permanent facts from model memory.
    """
    raise NotImplementedError
