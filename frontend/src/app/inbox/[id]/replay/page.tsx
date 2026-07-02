'use client';

export const dynamic = 'force-dynamic';

import React, { useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { api, DebateTrace, AgentRole, AgentAction, DebateTurn } from '@/lib/api';
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
import {
  ArrowLeft,
  ArrowRight,
  Play,
  Pause,
  SkipBack,
  SkipForward,
  FlaskConical,
  Plug,
  Puzzle,
  Database,
  Hash,
  Scale,
} from 'lucide-react';
import DebateAgent from './DebateAgent';
import { Loader } from '@/components/Loader';
import { useIsMobile } from '@/lib/useMediaQuery';
import { ROOM_BG, TABLE_SPRITE, getSpritePath, SpriteDirection } from '@/lib/replay/assets';
import { TABLE_CSS, SEATS, ROLE_SEAT } from '@/lib/replay/seminarRoom';
import styles from './replay.module.css';

const SPEEDS = [1, 1.5, 2] as const;
// Order the agents sit around the table (Arbitrator at the near head).
const SEAT_ORDER: AgentRole[] = ['arbitrator', 'assessor', 'advocate', 'auditor', 'gatekeeper'];
// Typewriter reveal speed for in-scene bubbles — deterministic off the playhead.
const REVEAL_MS_PER_CHAR = 14;
const BUBBLE_MAX_CHARS = 170;

function fmt(ms: number): string {
  const s = Math.floor(ms / 1000);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}

/** Listeners turn toward the active speaker; the speaker keeps their seat facing.
 *  Preserves the seat's depth component (front/rear) so heads turn naturally. */
function facingFor(role: AgentRole, speaker: AgentRole | null): SpriteDirection {
  const def = SEATS[ROLE_SEAT[role].seatKey].facing;
  if (!speaker || speaker === role) return def;
  const me = SEATS[ROLE_SEAT[role].seatKey];
  const sp = SEATS[ROLE_SEAT[speaker].seatKey];
  if (Math.abs(sp.x - me.x) < 3) return def;
  const depth = def.split('-')[0] as 'front' | 'rear';
  return `${depth}-${sp.x > me.x ? 'right' : 'left'}` as SpriteDirection;
}

export default function DebateReplayPage() {
  const params = useParams();
  const id = params?.id as string;
  const isMobile = useIsMobile();

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

  const turns = useMemo(() => trace?.turns ?? [], [trace]);
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
  const atStart = playheadMs === 0 && !playing;
  const finalTurn = turns[turns.length - 1];

  // Typewriter: characters revealed so far in the active bubble.
  const revealed = activeBeat ? Math.max(0, Math.floor((playheadMs - activeBeat.startMs) / REVEAL_MS_PER_CHAR)) : 0;
  const bubbleFull = activeTurn ? activeTurn.content.slice(0, BUBBLE_MAX_CHARS) : '';
  const bubbleShown = bubbleFull.slice(0, revealed) + (activeTurn && activeTurn.content.length > BUBBLE_MAX_CHARS && revealed >= BUBBLE_MAX_CHARS ? '…' : '');
  const bubbleTyping = revealed < bubbleFull.length;

  // Which agents does the active speaker cite right now? They react in-scene.
  const referencedRoles = useMemo(() => {
    if (!speaking || !activeTurn?.references_turn_ids) return new Set<AgentRole>();
    return new Set(activeTurn.references_turn_ids.map((i) => turns[i]?.role).filter(Boolean));
  }, [speaking, activeTurn, turns]);

  const speakerRole: AgentRole | null = speaking && activeTurn ? activeTurn.role : null;

  const logRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' });
  }, [activeIdx]);

  const seekToBeat = (i: number) => {
    if (i < 0 || i >= beats.length) return;
    setPlayheadMs(beats[i].startMs);
  };

  // Keyboard transport: space = play/pause, ←/→ = step turns.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === 'TEXTAREA' || (tag === 'INPUT' && (e.target as HTMLInputElement).type === 'text')) return;
      if (e.code === 'Space') {
        e.preventDefault();
        setPlaying((p) => {
          if (playheadMs >= totalMs && totalMs > 0) setPlayheadMs(0);
          return !p;
        });
      } else if (e.code === 'ArrowLeft') {
        e.preventDefault();
        seekToBeat(activeIdx - 1);
      } else if (e.code === 'ArrowRight') {
        e.preventDefault();
        seekToBeat(activeIdx + 1);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeIdx, playheadMs, totalMs, beats]);

  if (loading) {
    return <Loader fullscreen width={160} label="Loading debate…" />;
  }
  if (!trace) return null;

  const progressPct = totalMs > 0 ? (playheadMs / totalMs) * 100 : 0;

  return (
    <div style={{ height: '100dvh', display: 'flex', flexDirection: 'column', background: 'var(--surface-sunken)', overflow: 'hidden' }}>
      {/* ── Header ── */}
      <header style={hdr}>
        <div style={hdrInner}>
          <Link href={`/inbox/${id}`} style={backLink}>
            <ArrowLeft size={16} /> Outreach
          </Link>
          <span style={{ fontFamily: 'var(--font-display)', fontWeight: 600, color: 'var(--text-strong)', fontSize: 'var(--text-md)' }}>
            Debate Replay
          </span>
          {isDemo && (
            <span style={demoBadge}>
              <FlaskConical size={12} /> DEMO DATA
            </span>
          )}
          <span style={{ flex: 1 }} />
          <Link href={`/inbox/${id}`} style={reviewBtn}>
            Decision review <ArrowRight size={14} />
          </Link>
        </div>
      </header>

      {/* ── Body: stage card + rail card, gutters + centered ── */}
      <main
        style={{
          flex: 1,
          minHeight: 0,
          display: 'flex',
          flexDirection: isMobile ? 'column' : 'row',
          gap: 16,
          padding: isMobile ? '12px 16px' : '16px 24px',
          maxWidth: 1500,
          width: '100%',
          margin: '0 auto',
          boxSizing: 'border-box',
          overflow: isMobile ? 'auto' : 'hidden',
        }}
      >
        {/* ── STAGE CARD ── pixel-art seminar room; sprites, bubbles and the
            log all derive from the same playhead-driven, seekable clock. */}
        <section style={{ ...stageCard, flex: isMobile ? '0 0 auto' : 1.55 }}>
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
              const isActive = speakerRole === role;
              return (
                <DebateAgent
                  key={role}
                  role={role}
                  speaking={isActive}
                  referenced={referencedRoles.has(role)}
                  facing={facingFor(role, speakerRole)}
                  dot={meta.dot}
                  speechText={isActive ? bubbleShown : undefined}
                  typing={isActive && bubbleTyping}
                  entranceIndex={i}
                />
              );
            })}
          </div>

          {/* Start overlay — a proper opening beat instead of a bare caption. */}
          {atStart && (
            <div style={startOverlay}>
              <button
                onClick={() => setPlaying(true)}
                style={playCta}
                title="Play (space)"
              >
                <Play size={26} fill="currentColor" />
              </button>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--periwinkle-200)', letterSpacing: '0.08em' }}>
                WATCH THE SOCIETY DELIBERATE · SPACE
              </span>
            </div>
          )}

          {/* Decision lower-third at the end of the replay. */}
          {atEnd && finalTurn && (
            <div style={decisionThird}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontFamily: 'var(--font-mono)', fontSize: 10, color: '#BCC4EF', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                <Scale size={12} /> {ROLE_META.arbitrator.label} · Decision
              </span>
              <p style={{ margin: '6px 0 10px', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', color: '#F4F6FD', lineHeight: 1.55, display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                {finalTurn.content}
              </p>
              <Link href={`/inbox/${id}`} style={{ ...reviewBtn, background: 'var(--periwinkle-400)', color: 'var(--navy-900)' }}>
                Review & act on this decision <ArrowRight size={14} />
              </Link>
            </div>
          )}
        </section>

        {/* ── RAIL CARD ── participants header + evidence ledger + chat log ── */}
        <aside style={{ ...railCard, flex: 1, maxWidth: isMobile ? undefined : 430, minHeight: isMobile ? 380 : 0 }}>
          {/* Slack-style channel header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
            <Hash size={15} style={{ color: 'var(--text-muted)' }} />
            <span style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-strong)' }}>
              seminar-room
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>
              5 agents · replay
            </span>
            <span style={{ flex: 1 }} />
            <span style={{ display: 'flex', gap: 5 }}>
              {SEAT_ORDER.map((r) => (
                <span key={r} title={ROLE_META[r].label} style={{ width: 8, height: 8, borderRadius: '50%', background: ROLE_META[r].dot, opacity: visibleTurns.some((t) => t.role === r) ? 1 : 0.3, transition: 'opacity 300ms' }} />
              ))}
            </span>
          </div>

          {/* Evidence ledger */}
          <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
            <span style={railLabel}>EVIDENCE LEDGER</span>
            <div style={{ display: 'flex', gap: 6, margin: '8px 0 10px' }}>
              <Pill text={`${counts.verified} verified`} ink="var(--status-verified-ink)" bg="var(--status-verified-bg)" />
              <Pill text={`${counts.refuted} refuted`} ink="var(--status-refuted-ink)" bg="var(--status-refuted-bg)" />
              <Pill text={`${counts.open} open`} ink="var(--status-pending-ink)" bg="var(--status-pending-bg)" />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 5, maxHeight: 108, overflowY: 'auto' }}>
              {ledger.map((e) => (
                <div key={e.source_title} style={{ display: 'flex', alignItems: 'center', gap: 8 }} title={e.note ?? undefined}>
                  <span
                    style={{
                      width: 6, height: 6, borderRadius: '50%', flexShrink: 0,
                      background: e.status === 'verified' ? 'var(--status-verified)' : e.status === 'refuted' ? 'var(--status-refuted)' : 'var(--status-pending)',
                    }}
                  />
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-body)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {e.source_title}
                  </span>
                </div>
              ))}
              {ledger.length === 0 && (
                <span style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
                  No receipts surfaced yet.
                </span>
              )}
            </div>
          </div>

          {/* Slack-like chat log */}
          <div ref={logRef} style={{ flex: 1, overflowY: 'auto', padding: '8px 8px 14px', display: 'flex', flexDirection: 'column', gap: 2 }}>
            {visibleTurns.length === 0 && (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
                  Messages appear here as the debate plays.
                </span>
              </div>
            )}
            {visibleTurns.map((t, i) => {
              const meta = ROLE_META[t.role];
              const prev = visibleTurns[i - 1];
              const newRound = !prev || prev.round !== t.round;
              const isDecision = t.role === 'arbitrator';
              const refsActive = speaking && !!activeTurn?.references_turn_ids?.includes(i);
              const isActiveMsg = i === activeIdx && speaking;
              return (
                <React.Fragment key={i}>
                  {(newRound || isDecision) && (
                    <RoundDivider label={isDecision ? 'DECISION' : `ROUND ${t.round}`} />
                  )}
                  <ChatMessage
                    turn={t}
                    meta={meta}
                    time={fmt(beats[i]?.startMs ?? 0)}
                    active={isActiveMsg}
                    flash={refsActive}
                  />
                </React.Fragment>
              );
            })}
          </div>
        </aside>
      </main>

      {/* ── Transport ── */}
      <footer style={transport}>
        <div style={transportInner}>
          <button style={tBtn} onClick={() => seekToBeat(activeIdx - 1)} title="Previous turn (←)">
            <SkipBack size={15} />
          </button>
          <button
            style={{ ...tBtn, background: 'var(--navy-900)', color: '#fff', borderColor: 'var(--navy-900)' }}
            onClick={() => {
              if (atEnd) setPlayheadMs(0);
              setPlaying((p) => !p);
            }}
            title={playing ? 'Pause (space)' : 'Play (space)'}
          >
            {playing ? <Pause size={15} /> : <Play size={15} />}
          </button>
          <button style={tBtn} onClick={() => seekToBeat(activeIdx + 1)} title="Next turn (→)">
            <SkipForward size={15} />
          </button>

          <input
            type="range"
            min={0}
            max={totalMs}
            step={50}
            value={playheadMs}
            onChange={(e) => setPlayheadMs(Number(e.target.value))}
            className={styles.scrubber}
            style={{ background: `linear-gradient(to right, var(--navy-900) ${progressPct}%, var(--gray-200) ${progressPct}%)` }}
          />

          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)', minWidth: 92, textAlign: 'right' }}>
            {String(Math.max(0, activeIdx + 1)).padStart(2, '0')} / {String(turns.length).padStart(2, '0')} · {fmt(playheadMs)}
          </span>

          <div style={{ display: 'flex', gap: 4 }}>
            {SPEEDS.map((s) => (
              <button
                key={s}
                onClick={() => setSpeed(s)}
                style={{ ...tBtn, width: 'auto', padding: '0 9px', fontFamily: 'var(--font-mono)', fontSize: 11, background: speed === s ? 'var(--periwinkle-100)' : 'var(--surface-card)', color: speed === s ? 'var(--periwinkle-700)' : 'var(--text-muted)', borderColor: speed === s ? 'var(--periwinkle-300)' : 'var(--border-subtle)' }}
              >
                {s}×
              </button>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}

// ── Chat pieces ──────────────────────────────────────────────────────────────

function RoleAvatar({ role, bg }: { role: AgentRole; bg: string }) {
  const sprite = ROLE_SEAT[role].sprite;
  return (
    <div className={styles.avatarBox} style={{ background: bg }}>
      <img src={getSpritePath(sprite, 'front-left')} alt={role} className={styles.avatarSprite} draggable={false} />
    </div>
  );
}

function ChatMessage({
  turn,
  meta,
  time,
  active,
  flash,
}: {
  turn: DebateTurn;
  meta: (typeof ROLE_META)[AgentRole];
  time: string;
  active: boolean;
  flash: boolean;
}) {
  return (
    <div
      className={`${styles.chatRow} ${flash ? styles.chatRowFlash : ''}`}
      style={{
        background: flash ? `${meta.dot}14` : active ? meta.bg : 'transparent',
        color: meta.dot, // currentColor drives the flash ring
      }}
    >
      <RoleAvatar role={turn.role} bg={meta.bg} />
      <div style={{ minWidth: 0, flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 7 }}>
          <span style={{ fontFamily: 'var(--font-sans)', fontSize: 12.5, fontWeight: 700, color: meta.ink }}>
            {meta.label}
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: meta.dot, border: `1px solid ${meta.dot}55`, borderRadius: 4, padding: '0 4px' }}>
            R{turn.round}
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-subtle)' }}>{time}</span>
        </div>
        <p style={{ margin: '3px 0 0', fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-body)', lineHeight: 1.5, overflowWrap: 'break-word' }}>
          {turn.content}
        </p>
        <ActionChips actions={turn.actions} />
      </div>
    </div>
  );
}

function RoundDivider({ label }: { label: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 10px 6px' }}>
      <span style={{ flex: 1, height: 1, background: 'var(--border-subtle)' }} />
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-muted)', letterSpacing: '0.08em' }}>
        {label}
      </span>
      <span style={{ flex: 1, height: 1, background: 'var(--border-subtle)' }} />
    </div>
  );
}

// Tool chips — colors mirror the agent-lane discipline (plum/teal/gray families).
const ACTION_STYLE: Record<AgentAction['kind'], { color: string; Icon: typeof Plug; label: string }> = {
  mcp: { color: '#6E5B92', Icon: Plug, label: 'MCP' },
  skill: { color: '#2F7D72', Icon: Puzzle, label: 'SKILL' },
  retrieval: { color: '#6C7589', Icon: Database, label: 'RAG' },
};

function ActionChips({ actions }: { actions: AgentAction[] }) {
  if (!actions || actions.length === 0) return null;
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginTop: 6 }}>
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
              borderRadius: 'var(--radius-sm)', padding: '2px 6px', maxWidth: '100%',
            }}
          >
            <s.Icon size={10} style={{ flexShrink: 0 }} />
            <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {s.label} · {a.name}
              {a.detail ? ` — ${a.detail}` : ''}
            </span>
          </span>
        );
      })}
    </div>
  );
}

function Pill({ text, ink, bg }: { text: string; ink: string; bg: string }) {
  return (
    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: ink, background: bg, borderRadius: 'var(--radius-sm)', padding: '2px 8px' }}>
      {text}
    </span>
  );
}

// ── styles ──
const hdr: React.CSSProperties = { borderBottom: '1px solid var(--border-subtle)', background: 'var(--surface-card)' };
const hdrInner: React.CSSProperties = { display: 'flex', alignItems: 'center', gap: 14, padding: '12px 24px', maxWidth: 1500, margin: '0 auto' };
const backLink: React.CSSProperties = { display: 'inline-flex', alignItems: 'center', gap: 6, textDecoration: 'none', color: 'var(--text-muted)', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)' };
const reviewBtn: React.CSSProperties = { display: 'inline-flex', alignItems: 'center', gap: 6, textDecoration: 'none', background: 'var(--navy-900)', color: '#fff', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-xs)', fontWeight: 600, padding: '7px 12px', borderRadius: 'var(--radius-md)' };
const demoBadge: React.CSSProperties = { display: 'inline-flex', alignItems: 'center', gap: 4, fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--status-pending-ink)', background: 'var(--status-pending-bg)', borderRadius: 'var(--radius-sm)', padding: '3px 7px' };
const stageCard: React.CSSProperties = { position: 'relative', minWidth: 0, background: 'var(--navy-950)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-xl)', overflow: 'hidden', boxShadow: 'var(--shadow-md)', display: 'flex', alignItems: 'center', justifyContent: 'center' };
const railCard: React.CSSProperties = { display: 'flex', flexDirection: 'column', minWidth: 300, background: 'var(--surface-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-xl)', overflow: 'hidden', boxShadow: 'var(--shadow-sm)' };
const railLabel: React.CSSProperties = { fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-muted)', letterSpacing: '0.05em' };
const startOverlay: React.CSSProperties = { position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 14, background: 'rgba(3, 11, 29, 0.45)', zIndex: 300 };
const playCta: React.CSSProperties = { display: 'flex', alignItems: 'center', justifyContent: 'center', width: 64, height: 64, borderRadius: '50%', border: '2px solid var(--periwinkle-400)', background: 'var(--navy-900)', color: 'var(--periwinkle-200)', cursor: 'pointer', boxShadow: '0 0 24px rgba(161, 171, 232, 0.35)' };
const decisionThird: React.CSSProperties = { position: 'absolute', left: 14, right: 14, bottom: 14, zIndex: 300, background: 'rgba(6, 21, 49, 0.93)', border: '1px solid rgba(161, 171, 232, 0.35)', borderRadius: 'var(--radius-lg)', padding: '12px 16px', backdropFilter: 'blur(3px)' };
const transport: React.CSSProperties = { borderTop: '1px solid var(--border-subtle)', background: 'var(--surface-card)' };
const transportInner: React.CSSProperties = { display: 'flex', alignItems: 'center', gap: 10, padding: '10px 24px', maxWidth: 1500, margin: '0 auto' };
const tBtn: React.CSSProperties = { display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 32, height: 32, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', background: 'var(--surface-card)', color: 'var(--text-body)', cursor: 'pointer' };
