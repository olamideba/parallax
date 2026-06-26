from __future__ import annotations

import hashlib
import hmac
import re


def derive_intake_address(
    professor_id: str,
    professor_email: str,
    secret: str,
    domain: str,
) -> str:
    """Deterministically derive a professor's unique inbound intake address.

    The token is an HMAC of the professor id under the shared secret, so the
    same professor always maps to the same address and the address cannot be
    forged without the secret.
    """
    token = hmac.new(
        secret.encode(),
        professor_id.encode(),
        hashlib.sha256,
    ).hexdigest()[:16]
    local = professor_email.split("@", 1)[0]
    local = re.sub(r"[^a-zA-Z0-9]", "", local).lower() or "prof"
    return f"{local}-{token}@{domain}"
