from __future__ import annotations

# Known forwarding-confirmation sender addresses, by provider.
# Gmail is verified from real payloads; extend as others are confirmed empirically.
_CONFIRMATION_SENDERS = frozenset(
    {
        "forwarding-noreply@google.com",  # Gmail / Google Workspace
        "mail-noreply@google.com",  # Gmail (alternate)
    }
)

# Conservative cross-provider fallback: a forwarding-related subject AND an
# automated-looking sender local-part. Requires BOTH to avoid flagging real
# applicants who merely mention "forwarding".
_SUBJECT_HINTS = (
    "forwarding confirmation",
    "forwarding verification",
    "verify your forwarding",
    "confirm forwarding",
    "forwarding request",
    "verify your email forwarding",
)
_AUTOMATED_LOCALPARTS = (
    "noreply",
    "no-reply",
    "no_reply",
    "forwarding",
    "postmaster",
    "mailer-daemon",
    "mailerdaemon",
    "donotreply",
)


def is_forwarding_confirmation(sender_email: str, subject: str | None) -> bool:
    sender = (sender_email or "").strip().lower()
    if sender in _CONFIRMATION_SENDERS:
        return True

    subject_l = (subject or "").lower()
    local_part = sender.split("@", 1)[0]
    has_hint = any(hint in subject_l for hint in _SUBJECT_HINTS)
    looks_automated = any(token in local_part for token in _AUTOMATED_LOCALPARTS)
    return has_hint and looks_automated
