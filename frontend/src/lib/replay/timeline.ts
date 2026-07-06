import { AgentRole, DebateTurn, Receipt } from '@/lib/api';

// The replay is a deterministic function of a single `playheadMs`. We compile
// turns[] into beats with start/end offsets; the UI derives the active speaker,
// the visible log, and the evidence ledger purely from the playhead. This is
// what makes the transport seekable (scrub / step / speed) — unlike fire-and-
// forget setTimeout, which can only play forward once.

export interface Beat {
  turnIndex: number;
  startMs: number;
  endMs: number;
  round: number;
  role: AgentRole;
}

const GAP_MS = 600;
const BASE_MS = 2500;
const PER_CHAR_MS = 18;
const MAX_TURN_MS = 8500;

export function turnDuration(turn: DebateTurn): number {
  // Real synthesized audio wins — the beat is exactly as long as the speech.
  // Absent audio (synthesis pending/failed, or older traces), fall back to the
  // character-count heuristic so the replay still plays as a silent beat.
  if (turn.audio_duration_ms && turn.audio_duration_ms > 0) {
    return turn.audio_duration_ms;
  }
  return Math.min(MAX_TURN_MS, BASE_MS + turn.content.length * PER_CHAR_MS);
}

export function buildTimeline(turns: DebateTurn[]): Beat[] {
  let cursor = 0;
  return turns.map((turn, turnIndex) => {
    const startMs = cursor;
    const endMs = startMs + turnDuration(turn);
    cursor = endMs + GAP_MS;
    return { turnIndex, startMs, endMs, round: turn.round, role: turn.role };
  });
}

export function totalDuration(beats: Beat[]): number {
  return beats.length === 0 ? 0 : beats[beats.length - 1].endMs;
}

/** Index of the most recently started beat at `playheadMs`, or -1 before the first. */
export function activeBeatIndex(beats: Beat[], playheadMs: number): number {
  let idx = -1;
  for (let i = 0; i < beats.length; i++) {
    if (beats[i].startMs <= playheadMs) idx = i;
    else break;
  }
  return idx;
}

/** True while the active beat is still "speaking" (playhead within [start,end)). */
export function isSpeaking(beat: Beat, playheadMs: number): boolean {
  return playheadMs >= beat.startMs && playheadMs < beat.endMs;
}

// ── Evidence ledger ─────────────────────────────────────────────────────────
export type ReceiptStatus = 'verified' | 'refuted' | 'open';

export interface LedgerEntry {
  source_title: string;
  status: ReceiptStatus;
  note: string | null;
}

function statusOf(receipt: Receipt): ReceiptStatus {
  const note = (receipt.relevance_note ?? '').toLowerCase();
  if (/no match|refut|inflat|unverif|not found/.test(note)) return 'refuted';
  if (/verif|confirm|matched/.test(note)) return 'verified';
  return 'open';
}

/** Fold the receipts of all turns up to and including `lastTurnIndex` into a
 *  deduped ledger keyed by source. Later mentions win (a refute overrides an
 *  earlier verify), mirroring how the debate sharpens over rounds. */
export function buildLedger(turns: DebateTurn[], lastTurnIndex: number): LedgerEntry[] {
  const bySource = new Map<string, LedgerEntry>();
  for (let i = 0; i <= lastTurnIndex && i < turns.length; i++) {
    for (const r of turns[i].receipts) {
      bySource.set(r.source_title, {
        source_title: r.source_title,
        status: statusOf(r),
        note: r.relevance_note,
      });
    }
  }
  return [...bySource.values()];
}

export function ledgerCounts(entries: LedgerEntry[]): Record<ReceiptStatus, number> {
  return entries.reduce(
    (acc, e) => ({ ...acc, [e.status]: acc[e.status] + 1 }),
    { verified: 0, refuted: 0, open: 0 } as Record<ReceiptStatus, number>,
  );
}

// Mirrors the --agent-N lane tokens in colors.css (hex literals kept so
// alpha-suffix compositing like `${dot}22` works in inline styles).
// `label` is the agent's human name (shown prominently); `title` is its role,
// shown as a small badge. Names mirror the backend personas
// (backend/src/adapters/qwen_cloud/personas.py) — keep the two in sync.
export const ROLE_META: Record<AgentRole, { label: string; title: string; dot: string; ink: string; bg: string }> = {
  advocate: { label: 'leslie', title: 'Advocate', dot: '#4F5BB8', ink: '#3C46A0', bg: '#ECEEFA' },      // --agent-1
  auditor: { label: 'karen', title: 'Auditor', dot: '#2F7D72', ink: '#236258', bg: '#E5F1EF' },    // --agent-2
  assessor: { label: 'lami', title: 'Assessor', dot: '#9A6326', ink: '#7E501C', bg: '#F5EDE2' }, // --agent-3
  arbitrator: { label: 'dumbledore', title: 'Arbitrator', dot: '#6E5B92', ink: '#574576', bg: '#F0EDF6' },      // --agent-4
  gatekeeper: { label: 'kumar', title: 'Gatekeeper', dot: '#6C7589', ink: '#4B5468', bg: '#EEF1F6' },     // gray lane
};
