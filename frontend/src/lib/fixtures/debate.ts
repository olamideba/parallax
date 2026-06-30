import { DebateTrace } from '@/lib/api';

// Demo fixture mirroring the reference mockup (Wei Chen). Used by the replay
// surface when the backend has no trace yet (engine still in progress) so the
// "wow" surface is always demoable. Turn order matters: `references_turn_ids`
// point at earlier indices in `turns[]`, which is what proves cross-round
// reasoning (§5.4 — "agents reference each other's prior-round arguments").
const t0 = '2026-06-29T10:00:00Z';
const at = (s: number) => new Date(Date.parse(t0) + s * 1000).toISOString();

export const SAMPLE_DEBATE: DebateTrace = {
  id: 'fixture-debate-0001',
  outreach_id: 'fixture-outreach-0001',
  professor_id: 'fixture-professor-0001',
  round_cap: 3,
  terminated_at_round: 3,
  started_at: at(0),
  ended_at: at(60),
  turns: [
    // ── Round 0 — Gatekeeper pre-filter (not a debater; promotes into the room)
    {
      round: 0,
      role: 'gatekeeper',
      content:
        'Outreach is specific, names a real paper, and proposes a concrete extension. Not slop — promoting to full review.',
      receipts: [],
      actions: [{ kind: 'skill', name: 'triage', detail: 'lightweight slop filter', source: 'gatekeeper-skill' }],
      references_turn_ids: [],
      created_at: at(2),
    },
    // ── Round 1 — opening positions
    {
      round: 1,
      role: 'advocate',
      content:
        'The candidate grounds their outreach in your specific line of work, not a generic pitch. They propose extending your sparse-attention kernels to long-context retrieval — a direction your lab has signalled.',
      receipts: [
        {
          source_title: '[P-04] ICML 2023 — Sparse-Attention Kernels',
          chunk_text:
            'We introduce block-sparse attention kernels that reduce memory by 4x at 8k context...',
          relevance_note: 'Outreach references this paper directly.',
        },
      ],
      actions: [
        { kind: 'retrieval', name: 'publication-rag', detail: 'matched [P-04] ICML 2023', source: 'pgvector' },
      ],
      references_turn_ids: [],
      created_at: at(8),
    },
    {
      round: 1,
      role: 'auditor',
      content:
        'I verified the publication record. Two of the three claimed first-author papers are confirmed and topically adjacent. The third could not be located in any index.',
      receipts: [
        {
          source_title: '[P-09] arXiv:2402.11 — Long-Context Retrieval',
          chunk_text: 'Author list confirms first-authorship; topic is attention over long contexts.',
          relevance_note: 'verified — 2 of 3 claimed papers matched, both on attention methods.',
        },
        {
          source_title: '[P-11] (claimed) Efficient Transformers Survey',
          chunk_text: '',
          relevance_note: 'no match — not found in any index; possible inflated/AI-padded claim.',
        },
      ],
      actions: [
        { kind: 'mcp', name: 'scholarly-index', detail: 'arXiv:2402.11 — match', source: 'arxiv' },
        { kind: 'mcp', name: 'scholarly-index', detail: '[P-11] — no match', source: 'crossref' },
        { kind: 'skill', name: 'claim-verification', detail: '2 of 3 claims confirmed', source: 'auditor-skill' },
      ],
      references_turn_ids: [1],
      created_at: at(15),
    },
    {
      round: 1,
      role: 'assessor',
      content:
        'Capacity check: you have 2 of 3 PhD slots open this cycle, and the candidate is self-funded via a national scholarship — so no funding objection. Feasible to take.',
      receipts: [
        {
          source_title: 'Lab profile — declared capacity',
          chunk_text: '3 PhD slots, 2 open. Recruiting topics: efficient attention, retrieval.',
          relevance_note: 'verified against onboarding capacity.',
        },
      ],
      actions: [
        { kind: 'skill', name: 'capacity-check', detail: '2 of 3 slots open', source: 'lab-profile' },
      ],
      references_turn_ids: [],
      created_at: at(22),
    },
    // ── Round 2 — cross-examination (turns build on Round 1)
    {
      round: 2,
      role: 'advocate',
      content:
        'On the unmatched paper — the candidate may have mis-cited a workshop version. Their two verified papers already establish genuine fit; the case does not depend on the third.',
      receipts: [],
      actions: [],
      references_turn_ids: [2],
      created_at: at(30),
    },
    {
      round: 2,
      role: 'auditor',
      content:
        'Noted, but the unmatched claim is exactly the failure mode this review exists to catch. I will flag it for the professor rather than discard it — an inflated record is a real signal.',
      receipts: [
        {
          source_title: '[P-11] (claimed) Efficient Transformers Survey',
          chunk_text: '',
          relevance_note: 'refuted — flag to professor; do not treat as established.',
        },
      ],
      actions: [
        { kind: 'skill', name: 'claim-verification', detail: 'flag inflated claim', source: 'auditor-skill' },
      ],
      references_turn_ids: [4],
      created_at: at(38),
    },
    {
      round: 2,
      role: 'assessor',
      content:
        'No mobility blocker found via live lookup (dated 2026-06-28): the candidate’s scholarship covers relocation and no current visa restriction applies to their country. Presented as a dated lookup, not asserted fact.',
      receipts: [
        {
          source_title: 'Live lookup — mobility/visa (dated 2026-06-28)',
          chunk_text: 'No current restriction for candidate nationality; scholarship covers relocation.',
          relevance_note: 'verified via live, date-stamped lookup.',
        },
      ],
      actions: [
        { kind: 'mcp', name: 'web-search', detail: 'mobility/visa lookup — dated 2026-06-28', source: 'web-search' },
        { kind: 'skill', name: 'mobility-check', detail: 'date-stamped, not asserted', source: 'assessor-skill' },
      ],
      references_turn_ids: [3],
      created_at: at(46),
    },
    // ── Round 3 — Arbitrator synthesis (the decision)
    {
      round: 3,
      role: 'arbitrator',
      content:
        'Genuine, well-grounded fit (2 verified papers on your exact methods) with one flagged claim and no capacity or funding objection. Recommendation: INVITE, with a note asking the candidate to clarify the third citation.',
      receipts: [],
      actions: [],
      references_turn_ids: [5, 6, 7],
      created_at: at(56),
    },
  ],
};
