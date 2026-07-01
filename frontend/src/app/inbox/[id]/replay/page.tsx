'use client';

export const dynamic = 'force-dynamic';

import React, { useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { api, DebateTrace, AgentRole, AgentAction } from '@/lib/api';
import { SAMPLE_DEBATE } from '@/lib/fixtures/debate';
import {
  buildTimeline,
  totalDuration,
  activeBeatIndex,
  isSpeaking,
  buildLedger,
  ledgerCounts,
  ROLE_META,
} from '@/lib/replay/timeline';
import { ArrowLeft, Play, Pause, SkipBack, SkipForward, FlaskConical, Plug, Puzzle, Database } from 'lucide-react';
import DebateAgent from './DebateAgent';
import { Loader } from '@/components/Loader';
import { ROOM_BG, TABLE_SPRITE } from '@/lib/replay/assets';
import { TABLE_CSS } from '@/lib/replay/seminarRoom';
import styles from './replay.module.css';

const SPEEDS = [1, 1.5, 2] as const;
// Order the agents sit around the table (Arbitrator at the head).
const SEAT_ORDER: AgentRole[] = ['arbitrator', 'assessor', 'advocate', 'auditor', 'gatekeeper'];

function fmt(ms: number): string {
  const s = Math.floor(ms / 1000);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}

export default function DebateReplayPage() {
  const params = useParams();
  const id = params?.id as string;

  const [trace, setTrace] = useState<DebateTrace | null>(null);
  const [isDemo, setIsDemo] = useState(false);
  const [loading, setLoading] = useState(true);

  // Transport state
  const [playheadMs, setPlayheadMs] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState<(typeof SPEEDS)[number]>(1);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await api.getDebateTrace(id);
        if (!cancelled) setTrace(data);
      } catch {
        // No trace yet (engine in progress) — fall back to the demo fixture so
        // the wow surface is always showable.
        if (!cancelled) {
          setTrace(SAMPLE_DEBATE);
          setIsDemo(true);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  const turns = trace?.turns ?? [];
  const beats = useMemo(() => buildTimeline(turns), [turns]);
  const totalMs = useMemo(() => totalDuration(beats), [beats]);

  // The replay clock — a single playhead advanced by rAF, scaled by speed.
  useEffect(() => {
    if (!playing) return;
    let raf = 0;
    let last = performance.now();
    const tick = (now: number) => {
      const dt = (now - last) * speed;
      last = now;
      setPlayheadMs((p) => {
        const next = p + dt;
        if (next >= totalMs) {
          setPlaying(false);
          return totalMs;
        }
        return next;
      });
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [playing, speed, totalMs]);

  // Derived render state — pure functions of the playhead.
  const activeIdx = activeBeatIndex(beats, playheadMs);
  const activeBeat = activeIdx >= 0 ? beats[activeIdx] : null;
  const activeTurn = activeBeat ? turns[activeBeat.turnIndex] : null;
  const speaking = activeBeat ? isSpeaking(activeBeat, playheadMs) : false;
  const visibleTurns = turns.slice(0, activeIdx + 1);
  const ledger = useMemo(() => buildLedger(turns, activeIdx), [turns, activeIdx]);
  const counts = ledgerCounts(ledger);
  const atEnd = playheadMs >= totalMs && totalMs > 0;
  const finalTurn = turns[turns.length - 1];

  const logRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' });
  }, [activeIdx]);

  const seekToBeat = (i: number) => {
    if (i < 0 || i >= beats.length) return;
    setPlayheadMs(beats[i].startMs);
  };

  if (loading) {
    return (
      <Loader fullscreen width={160} label="Loading debate…" />
    );
  }
  if (!trace) return null;

  return (
    <div style={{ height: '100dvh', display: 'flex', flexDirection: 'column', background: 'var(--surface-sunken)', overflow: 'hidden' }}>
      {/* Header */}
      <header style={hdr}>
        <Link href={`/inbox/${id}`} style={backLink}>
          <ArrowLeft size={16} /> Outreach
        </Link>
        <span style={{ fontFamily: 'var(--font-display)', fontWeight: 600, color: 'var(--text-strong)' }}>
          Debate Replay
        </span>
        {isDemo && (
          <span style={demoBadge}>
            <FlaskConical size={12} /> DEMO DATA
          </span>
        )}
        <span style={{ flex: 1 }} />
        <Link href={`/inbox/${id}`} style={{ ...backLink, color: 'var(--navy-900)' }}>
          Decision review →
        </Link>
      </header>

      {/* Body: stage (left) + rail (right) */}
      <main style={{ flex: 1, display: 'grid', gridTemplateColumns: 'minmax(0, 1.6fr) minmax(300px, 1fr)', gap: 0, minHeight: 0, overflow: 'hidden' }}>
        {/* ── STAGE ── pixel-art seminar room; sprites + speech bubble animate
            off the same playhead-driven clock as the transport and log. */}
        <section style={stage}>
          <div className={styles.roomStage}>
            <img src={ROOM_BG} alt="" className={styles.roomBackground} />
            <img
              src={TABLE_SPRITE}
              alt=""
              className={styles.tableProp}
              style={{ left: `${TABLE_CSS.left}%`, top: `${TABLE_CSS.top}%`, width: `${TABLE_CSS.width}%`, zIndex: TABLE_CSS.zIndex }}
            />
            {SEAT_ORDER.map((role, i) => {
              const meta = ROLE_META[role];
              const isActive = activeTurn?.role === role && speaking;
              const hasSpoken = visibleTurns.some((t) => t.role === role);
              return (
                <DebateAgent
                  key={role}
                  role={role}
                  speaking={isActive}
                  hasSpoken={hasSpoken}
                  dot={meta.dot}
                  speechText={isActive ? activeTurn?.content : undefined}
                  idleDelay={i * 0.45}
                />
              );
            })}
          </div>

          {/* Active speaker's full-text bubble */}
          <div style={bubbleWrap}>
            {activeTurn && speaking ? (
              <div style={{ ...bubble, borderColor: `${ROLE_META[activeTurn.role].dot}55` }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: ROLE_META[activeTurn.role].dot, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  {ROLE_META[activeTurn.role].label} · round {activeBeat?.round}
                </span>
                <p style={{ margin: '6px 0 0', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', color: 'var(--text-body)', lineHeight: 1.5 }}>
                  {activeTurn.content}
                </p>
                <ActionChips actions={activeTurn.actions} />
              </div>
            ) : atEnd ? (
              <div style={{ ...bubble, borderColor: `${ROLE_META.arbitrator.dot}55` }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: ROLE_META.arbitrator.dot, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Decision
                </span>
                <p style={{ margin: '6px 0 0', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', color: 'var(--text-body)', lineHeight: 1.5 }}>
                  {finalTurn?.content}
                </p>
                <Link href={`/inbox/${id}`} style={{ ...backLink, color: 'var(--navy-900)', marginTop: 10 }}>
                  Review & act on this decision →
                </Link>
              </div>
            ) : (
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
                Press play to watch the society deliberate.
              </span>
            )}
          </div>
        </section>

        {/* ── RAIL ── evidence ledger + chat log ── */}
        <aside style={rail}>
          <div style={{ padding: '16px 18px', borderBottom: '1px solid var(--border-subtle)' }}>
            <span style={railLabel}>EVIDENCE LEDGER</span>
            <div style={{ display: 'flex', gap: 8, margin: '8px 0 12px' }}>
              <Pill text={`${counts.verified} verified`} color="var(--status-verified-ink)" />
              <Pill text={`${counts.refuted} refuted`} color="var(--status-critical-ink)" />
              <Pill text={`${counts.open} open`} color="var(--text-muted)" />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {ledger.map((e) => (
                <div key={e.source_title} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span
                    style={{
                      width: 6, height: 6, borderRadius: '50%', flexShrink: 0,
                      background: e.status === 'verified' ? 'var(--status-verified-ink)' : e.status === 'refuted' ? 'var(--status-critical-ink)' : 'var(--text-muted)',
                    }}
                  />
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-body)' }}>{e.source_title}</span>
                </div>
              ))}
              {ledger.length === 0 && <span style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>No receipts surfaced yet.</span>}
            </div>
          </div>

          <span style={{ ...railLabel, padding: '14px 18px 6px' }}>CHAT LOG</span>
          <div ref={logRef} style={{ flex: 1, overflowY: 'auto', padding: '0 18px 18px', display: 'flex', flexDirection: 'column', gap: 10 }}>
            {visibleTurns.map((t, i) => {
              const meta = ROLE_META[t.role];
              const refsActive = activeTurn?.references_turn_ids?.includes(i) && speaking;
              return (
                <div
                  key={i}
                  style={{
                    borderLeft: `2px solid ${meta.dot}`,
                    paddingLeft: 10,
                    background: refsActive ? `${meta.dot}14` : 'transparent',
                    borderRadius: 4,
                    transition: 'background 200ms',
                  }}
                >
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: meta.dot, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    {meta.label} · r{t.round}
                  </span>
                  <p style={{ margin: '2px 0 0', fontFamily: 'var(--font-sans)', fontSize: 12, color: 'var(--text-body)', lineHeight: 1.45 }}>
                    {t.content}
                  </p>
                  <ActionChips actions={t.actions} />
                </div>
              );
            })}
          </div>
        </aside>
      </main>

      {/* ── TRANSPORT ── */}
      <footer style={transport}>
        <button style={tBtn} onClick={() => seekToBeat(activeIdx - 1)} title="Previous turn">
          <SkipBack size={16} />
        </button>
        <button
          style={{ ...tBtn, background: 'var(--navy-900)', color: '#fff' }}
          onClick={() => {
            if (atEnd) setPlayheadMs(0);
            setPlaying((p) => !p);
          }}
          title={playing ? 'Pause' : 'Play'}
        >
          {playing ? <Pause size={16} /> : <Play size={16} />}
        </button>
        <button style={tBtn} onClick={() => seekToBeat(activeIdx + 1)} title="Next turn">
          <SkipForward size={16} />
        </button>

        <input
          type="range"
          min={0}
          max={totalMs}
          step={50}
          value={playheadMs}
          onChange={(e) => setPlayheadMs(Number(e.target.value))}
          style={{ flex: 1, accentColor: 'var(--navy-900)' }}
        />

        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)', minWidth: 92, textAlign: 'right' }}>
          {String(Math.max(0, activeIdx + 1)).padStart(2, '0')} / {String(turns.length).padStart(2, '0')} · {fmt(playheadMs)}
        </span>

        <div style={{ display: 'flex', gap: 4 }}>
          {SPEEDS.map((s) => (
            <button
              key={s}
              onClick={() => setSpeed(s)}
              style={{ ...tBtn, width: 'auto', padding: '0 8px', fontFamily: 'var(--font-mono)', fontSize: 11, background: speed === s ? 'var(--navy-50)' : 'var(--surface-card)', color: speed === s ? 'var(--navy-900)' : 'var(--text-muted)' }}
            >
              {s}×
            </button>
          ))}
        </div>
      </footer>
    </div>
  );
}

const ACTION_STYLE: Record<AgentAction['kind'], { color: string; Icon: typeof Plug; label: string }> = {
  mcp: { color: '#8b5cf6', Icon: Plug, label: 'MCP' },
  skill: { color: '#0d9488', Icon: Puzzle, label: 'SKILL' },
  retrieval: { color: '#64748b', Icon: Database, label: 'RAG' },
};

function ActionChips({ actions }: { actions: AgentAction[] }) {
  if (!actions || actions.length === 0) return null;
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginTop: 7 }}>
      {actions.map((a, i) => {
        const s = ACTION_STYLE[a.kind];
        return (
          <span
            key={i}
            title={a.detail ?? undefined}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 4,
              fontFamily: 'var(--font-mono)', fontSize: 9.5, color: s.color,
              background: `${s.color}12`, border: `1px solid ${s.color}40`,
              borderRadius: 'var(--radius-sm)', padding: '2px 6px',
            }}
          >
            <s.Icon size={10} />
            {s.label} · {a.name}
            {a.detail ? <span style={{ color: 'var(--text-muted)' }}>— {a.detail}</span> : null}
          </span>
        );
      })}
    </div>
  );
}

function Pill({ text, color }: { text: string; color: string }) {
  return (
    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color, background: `${color === 'var(--text-muted)' ? 'rgba(0,0,0,0.04)' : 'transparent'}`, border: `1px solid ${color}`, borderRadius: 'var(--radius-sm)', padding: '2px 8px' }}>
      {text}
    </span>
  );
}

// ── styles ──
const hdr: React.CSSProperties = { display: 'flex', alignItems: 'center', gap: 14, padding: '14px 20px', borderBottom: '1px solid var(--border-subtle)', background: 'var(--surface-card)' };
const backLink: React.CSSProperties = { display: 'inline-flex', alignItems: 'center', gap: 6, textDecoration: 'none', color: 'var(--text-muted)', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)' };
const demoBadge: React.CSSProperties = { display: 'inline-flex', alignItems: 'center', gap: 4, fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--status-triage-ink)', border: '1px solid var(--status-triage-ink)', borderRadius: 'var(--radius-sm)', padding: '2px 6px' };
const stage: React.CSSProperties = { display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'hidden' };
const bubbleWrap: React.CSSProperties = { display: 'flex', justifyContent: 'center', alignItems: 'flex-end', flex: '0 0 auto', minHeight: 90, maxHeight: 180, padding: '10px 20px 16px', overflow: 'hidden' };
const bubble: React.CSSProperties = { maxWidth: 560, background: 'var(--surface-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-xl)', padding: '14px 18px', boxShadow: 'var(--shadow-md)', display: 'flex', flexDirection: 'column' };
const rail: React.CSSProperties = { display: 'flex', flexDirection: 'column', borderLeft: '1px solid var(--border-subtle)', background: 'var(--surface-card)', minHeight: 0 };
const railLabel: React.CSSProperties = { fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-muted)', letterSpacing: '0.05em' };
const transport: React.CSSProperties = { display: 'flex', alignItems: 'center', gap: 10, padding: '12px 20px', borderTop: '1px solid var(--border-subtle)', background: 'var(--surface-card)' };
const tBtn: React.CSSProperties = { display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 34, height: 34, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', background: 'var(--surface-card)', color: 'var(--text-body)', cursor: 'pointer' };
