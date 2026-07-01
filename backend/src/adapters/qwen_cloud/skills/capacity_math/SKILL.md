---
name: capacity-math
description: Use when a debate agent needs to reason about whether the professor has room for another student — deterministic arithmetic over declared capacity, not a judgment call.
---

# Capacity Math

Compute effective open capacity from the professor's declared numbers. This is
arithmetic, not opinion — never round in the candidate's favor.

## Procedure

1. `effective_open_slots = max(0, open_slots - students_committed)`.
2. If `effective_open_slots == 0`: there is no open slot. Say so plainly instead
   of hedging — implying "there might be room" when it's 0 is a fabrication.
3. `budget_amount` (if set) is informational context on funding capacity, not a
   per-student cost — do not divide it by an assumed cost unless one is given.
4. Report `effective_open_slots` and, when relevant, whether slot count or
   budget is the binding constraint.

This procedure is implemented directly in code
(`src/adapters/qwen_cloud/tools/capacity_math.py::assess_capacity`) — no LLM
call is needed to execute it. This file documents the algorithm for review and
for the Assessor's tool description.
