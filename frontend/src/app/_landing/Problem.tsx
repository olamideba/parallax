'use client';

import React from 'react';
import { useIsMobile } from '@/lib/useMediaQuery';
import { displayFont, Eyebrow } from './ui';

const bodyStyle: React.CSSProperties = {
  fontSize: 'var(--text-md)',
  lineHeight: 'var(--leading-relaxed)',
  color: 'var(--text-body)',
  margin: '0 0 var(--space-4)',
};

const h2Style: React.CSSProperties = {
  ...displayFont,
  fontSize: 'clamp(1.35rem, 2.2vw, 1.75rem)',
  color: 'var(--text-strong)',
  margin: 'var(--space-3) 0 var(--space-4)',
};

/* Show, don't tell: what lands in the inbox vs what Parallax hands back. */
function Comparison({ isMobile }: { isMobile: boolean }) {
  const cardBase: React.CSSProperties = {
    borderRadius: 'var(--radius-lg)',
    padding: 'var(--space-5)',
    display: 'flex',
    flexDirection: 'column',
    gap: 'var(--space-3)',
  };
  const mono: React.CSSProperties = {
    fontFamily: 'var(--font-mono)',
    fontSize: 'var(--text-2xs)',
    letterSpacing: '0.06em',
  };

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr',
        gap: 'var(--space-4)',
        marginTop: 'var(--space-12)',
      }}
    >
      <div style={{ ...cardBase, background: 'var(--surface-ground)', border: '1px solid var(--border-default)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
          <span style={{ ...mono, color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
            What lands in your inbox
          </span>
          <span
            style={{
              ...mono,
              fontWeight: 600,
              textTransform: 'uppercase',
              color: 'var(--status-refuted-ink)',
              background: 'var(--status-refuted-bg)',
              borderRadius: 'var(--radius-pill)',
              padding: '3px 9px',
            }}
          >
            Mass-mail pattern
          </span>
        </div>
        <div style={{ ...mono, color: 'var(--text-subtle)' }}>
          from: eager.applicant@gmail.com
          <br />
          subj: Prospective PhD student — deeply inspired by your work
        </div>
        <p style={{ fontSize: 'var(--text-sm)', lineHeight: 'var(--leading-relaxed)', color: 'var(--text-muted)', fontStyle: 'italic', margin: 0 }}>
          &ldquo;Dear Esteemed Professor, I came across your groundbreaking research and was deeply
          inspired by your novel contributions to the field. I believe my background makes me an
          excellent fit for your prestigious lab&hellip;&rdquo;
        </p>
      </div>

      <div style={{ ...cardBase, background: 'var(--navy-900)', border: '1px solid var(--navy-700)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
          <span style={{ ...mono, color: 'var(--text-muted-inverse)', textTransform: 'uppercase', fontWeight: 600 }}>
            What Parallax hands back
          </span>
          <span
            style={{
              ...mono,
              fontWeight: 600,
              textTransform: 'uppercase',
              color: 'var(--white)',
              background: 'var(--status-verified)',
              borderRadius: 'var(--radius-pill)',
              padding: '3px 9px',
            }}
          >
            Strong fit
          </span>
        </div>
        <div style={{ ...displayFont, fontSize: 'var(--text-md)', color: 'var(--white)' }}>
          Recommend for review
        </div>
        <div style={{ ...mono, color: 'var(--periwinkle-200)', display: 'flex', flexDirection: 'column', gap: 6 }}>
          <span>✓ cites your 2025 retrieval-eval paper — verified against index</span>
          <span>✓ stated interest matches declared topic &ldquo;RAG evaluation&rdquo;</span>
          <span>• funding ask fits one open RA slot</span>
        </div>
      </div>
    </div>
  );
}

export default function Problem() {
  const isMobile = useIsMobile();

  return (
    <section id="problem" style={{ background: 'var(--surface-sunken)', padding: 'var(--space-24) var(--space-6)' }}>
      <div style={{ maxWidth: 'var(--container-lg)', margin: '0 auto' }}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: 'var(--space-12)',
          }}
        >
          <div>
            <Eyebrow color="var(--status-refuted-ink)">The problem</Eyebrow>
            <h2 style={h2Style}>A flood of outreach, no way to tell real from generated.</h2>
            <p style={{ ...bodyStyle, margin: 0 }}>
              There&rsquo;s admissions software for applications, and recruiting software for
              hiring — nothing for the flood of AI-generated outreach that lands before either
              process starts. Professors are left skimming thousands of near-identical messages
              by hand, for the rare candidate who actually fits.
            </p>
          </div>

          <div>
            <Eyebrow color="var(--status-verified-ink)">The solution</Eyebrow>
            <h2 style={h2Style}>A society of agents, grounded in your own work.</h2>
            <p style={{ ...bodyStyle, margin: 0 }}>
              Agents debate each email against your real work and capacity — an Arbitrator returns
              one verdict, evidence attached.
            </p>
          </div>
        </div>

        <Comparison isMobile={isMobile} />
      </div>
    </section>
  );
}
