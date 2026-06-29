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

export const ROLE_META: Record<AgentRole, { label: string; dot: string }> = {
  advocate: { label: 'Fit Analyst', dot: '#3b82f6' },
  auditor: { label: 'Claim Verifier', dot: '#10b981' },
  assessor: { label: 'Capacity & Scope', dot: '#f59e0b' },
  arbitrator: { label: 'Synthesis', dot: '#8b5cf6' },
  gatekeeper: { label: 'Gatekeeper', dot: '#94a3b8' },
};
