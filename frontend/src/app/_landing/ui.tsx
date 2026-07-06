'use client';

import React from 'react';

/* Shared landing type + eyebrow primitives. Panchang (--font-brand) is the
   single display face for every heading on the landing — hero, sections,
   footer labels — with the app's sans for body. */

export const displayFont: React.CSSProperties = {
  fontFamily: 'var(--font-brand)',
  fontWeight: 700,
  letterSpacing: '-0.01em',
  lineHeight: 'var(--leading-tight)',
};

export function Eyebrow({
  children,
  tone = 'light',
  color,
}: {
  children: React.ReactNode;
  tone?: 'light' | 'dark';
  color?: string;
}) {
  const onDark = tone === 'dark';
  return (
    <span
      style={{
        display: 'inline-block',
        fontFamily: 'var(--font-mono)',
        fontSize: 10,
        fontWeight: 600,
        letterSpacing: 'var(--tracking-caps)',
        textTransform: 'uppercase',
        lineHeight: 1.4,
        color: color ?? (onDark ? 'var(--periwinkle-300)' : 'var(--text-accent)'),
        background: onDark ? 'var(--surface-inverse-raised)' : 'var(--surface-accent)',
        border: `1px solid ${onDark ? 'var(--border-inverse)' : 'var(--border-accent)'}`,
        borderRadius: 'var(--radius-pill)',
        padding: '6px 12px',
      }}
    >
      {children}
    </span>
  );
}

/* Scroll reveal: sections rise in gently as they enter the viewport.
   One-shot, transform/opacity only, off under prefers-reduced-motion. */
export function Reveal({ children }: { children: React.ReactNode }) {
  const ref = React.useRef<HTMLDivElement>(null);
  const [st, setSt] = React.useState({ shown: false, reduce: false });

  React.useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      // Reveal immediately with no transition; async to avoid a cascading
      // render inside the effect body.
      const raf = requestAnimationFrame(() => setSt({ shown: true, reduce: true }));
      return () => cancelAnimationFrame(raf);
    }
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          setSt({ shown: true, reduce: false });
          obs.disconnect();
        }
      },
      { threshold: 0.12 },
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      style={
        st.reduce
          ? undefined
          : {
              opacity: st.shown ? 1 : 0,
              transform: st.shown ? 'translateY(0)' : 'translateY(18px)',
              transition: 'opacity 380ms var(--ease-out), transform 380ms var(--ease-out)',
            }
      }
    >
      {children}
    </div>
  );
}

/* Dashed vertical connector — the same dashed debate-traffic language as the
   hero orbit, reused between the How-it-Works rows. */
export function DashedConnector({ height = 44 }: { height?: number }) {
  return (
    <svg width="2" height={height} aria-hidden="true" style={{ display: 'block' }}>
      <line
        x1="1"
        y1="0"
        x2="1"
        y2={height}
        stroke="var(--periwinkle-500)"
        strokeWidth="2"
        strokeDasharray="3 7"
        strokeLinecap="round"
      />
    </svg>
  );
}
