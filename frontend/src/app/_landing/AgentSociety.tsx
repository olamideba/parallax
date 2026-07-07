'use client';

import React from 'react';
import { Mail } from 'lucide-react';
import { getSpritePath, AgentSprite, SpriteDirection } from '@/lib/replay/assets';
import { useIsMobile } from '@/lib/useMediaQuery';
import styles from './agentSociety.module.css';

/* Five agents on a pentagon around one inbound email — the same pixel-art
   sprites as the debate replay, so the landing's society IS the product's
   society. Faces always show: left half faces right (front-right), right
   half faces left (front-left), the top apex defaults to front-right; never
   a rear-* sprite. Label colors are the real --agent-* lane tokens. */

interface Node {
  label: string;
  sprite: AgentSprite;
  facing: SpriteDirection;
  pill: string; // label pill fill (-ink variant for AA white text)
  x: number;
  y: number;
}

const NODES: Node[] = [
  { label: 'Arbitrator', sprite: 'arbitrator', facing: 'front-right', pill: 'var(--agent-4-ink)', x: 50, y: 11 },
  { label: 'Auditor', sprite: 'auditor', facing: 'front-left', pill: 'var(--agent-2-ink)', x: 89, y: 39 },
  { label: 'Assessor', sprite: 'assessor', facing: 'front-left', pill: 'var(--agent-3-ink)', x: 73, y: 84 },
  { label: 'Advocate', sprite: 'advocate', facing: 'front-right', pill: 'var(--agent-1-ink)', x: 27, y: 84 },
  { label: 'Gatekeeper', sprite: 'gatekeeper', facing: 'front-right', pill: 'var(--gray-600)', x: 11, y: 39 },
];

const CENTER = { x: 50, y: 50 };
const SPRITE_H = 96;
const CENTER_DISC = 74;

export default function AgentSociety() {
  const stageRef = React.useRef<HTMLDivElement>(null);
  const isMobile = useIsMobile();
  const [inView, setInView] = React.useState(false);

  React.useEffect(() => {
    const el = stageRef.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          setInView(true);
          obs.disconnect();
        }
      },
      { threshold: 0.25 },
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  // Subtle scroll parallax between the lines layer and the nodes layer — a
  // couple dozen px of relative offset at most, driven through a CSS var so
  // the module CSS owns the per-layer factors. Off on mobile/reduced-motion.
  React.useEffect(() => {
    const el = stageRef.current;
    if (!el || isMobile) return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    let raf = 0;
    const onScroll = () => {
      if (raf) return;
      raf = requestAnimationFrame(() => {
        raf = 0;
        const p = Math.min(window.scrollY, 400) * 0.08;
        el.style.setProperty('--p', `${p.toFixed(1)}px`);
      });
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', onScroll);
      if (raf) cancelAnimationFrame(raf);
    };
  }, [isMobile]);

  return (
    <div
      ref={stageRef}
      className={`${styles.stage} ${inView ? styles.inView : ''}`}
      style={{
        // Aspect-locked and capped by viewport height so all five nodes stay
        // visible without scrolling at 800/900/1080px-tall viewports.
        aspectRatio: '1 / 1',
        width: 'min(100%, 520px, 62vh)',
        margin: '0 auto',
      }}
    >
      <div className={styles.linesLayer} aria-hidden="true">
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ width: '100%', height: '100%', overflow: 'visible' }}>
          {NODES.map((n, i) => (
            <line
              key={`spoke-${i}`}
              x1={CENTER.x}
              y1={CENTER.y}
              x2={n.x}
              y2={n.y}
              className={styles.line}
              stroke="var(--periwinkle-400)"
              strokeWidth={0.6}
              style={{ animationDelay: `${i * 0.4}s` }}
            />
          ))}
          {NODES.map((n, i) => {
            const next = NODES[(i + 1) % NODES.length];
            return (
              <line
                key={`ring-${i}`}
                x1={n.x}
                y1={n.y}
                x2={next.x}
                y2={next.y}
                className={styles.line}
                stroke="var(--periwinkle-500)"
                strokeWidth={0.4}
                style={{ animationDelay: `${i * 0.55 + 0.2}s` }}
              />
            );
          })}
        </svg>
      </div>

      <div className={styles.nodesLayer}>
        <div
          className={styles.centerNode}
          style={{ left: `${CENTER.x}%`, top: `${CENTER.y}%`, width: CENTER_DISC, height: CENTER_DISC }}
        >
          <span className={styles.pulseRing} aria-hidden="true" />
          <span
            role="img"
            aria-label="Inbound candidate email"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '100%',
              height: '100%',
              borderRadius: '50%',
              background: 'var(--periwinkle-400)',
              border: '2px solid var(--navy-900)',
              boxShadow: '0 0 0 2px var(--periwinkle-400)',
            }}
          >
            <Mail size={26} strokeWidth={2} color="var(--navy-900)" />
          </span>
        </div>

        {NODES.map((n, i) => (
          <div
            key={n.label}
            className={styles.node}
            style={{ left: `${n.x}%`, top: `${n.y}%`, animationDelay: `${i * 0.06}s` }}
          >
            <img
              src={getSpritePath(n.sprite, n.facing)}
              alt={`${n.label} agent`}
              draggable={false}
              className={styles.disc}
              style={{
                height: SPRITE_H,
                width: 'auto',
                imageRendering: 'pixelated',
                animationDelay: `${i * 0.6}s`,
                // Varied idle rhythm so the society never bobs in unison
                // (same trick as the debate replay).
                animationDuration: `${3.8 + i * 0.35}s`,
              }}
            />
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 9,
                fontWeight: 600,
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
                color: 'var(--white)',
                background: n.pill,
                borderRadius: 'var(--radius-pill)',
                padding: '3px 9px',
                whiteSpace: 'nowrap',
              }}
            >
              {n.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
