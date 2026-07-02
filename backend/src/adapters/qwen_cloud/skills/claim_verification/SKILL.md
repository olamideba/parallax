---
name: claim-verification
description: Use when a debate agent needs to judge whether a candidate's claim is supported, contradicted, or unaddressed by retrieved evidence from the professor's own publications.
---

# Claim Verification

Judge ONE candidate claim against a set of retrieved evidence chunks pulled from
the professor's own indexed publications.

## Procedure

1. Read the claim in isolation — do not assume context beyond what it states.
2. Read every retrieved chunk. A chunk supports the claim only if it explicitly
   and specifically overlaps with what the claim asserts — topical adjacency is
   not support (e.g. "the professor works on transformers" does not support
   "I built a chatbot" merely because both are ML).
3. Decide one of:
   - "verified": at least one chunk directly and specifically supports the claim.
   - "refuted": the retrieved evidence directly contradicts the claim.
   - "unclear": no retrieved evidence bears on the claim either way.
4. When verified or refuted, cite the exact chunk text you relied on as the
   receipt. Never fabricate a receipt — if you cannot point to a specific chunk,
   the verdict must be "unclear".
5. Be conservative: a candidate's claim about their OWN work (e.g. "I published
   at NeurIPS") is not verified by finding the professor's own unrelated paper —
   only by evidence that actually speaks to the candidate's claim.
