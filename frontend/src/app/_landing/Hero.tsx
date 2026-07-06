'use client';

import React from 'react';
import Link from 'next/link';
import { Button } from '@/components/Button';
import { useIsMobile } from '@/lib/useMediaQuery';
import AgentSociety from './AgentSociety';
import { HACKATHON_LINE } from './constants';
import { displayFont, Eyebrow } from './ui';

export default function Hero({ authed = false }: { authed?: boolean }) {
  const isMobile = useIsMobile();
  const ctaHref = authed ? '/inbox' : '/signup';
  const ctaLabel = authed ? 'Go to inbox →' : 'Try it free →';

  const scrollToDemo = () => {
    const el = document.querySelector('#demo');
    if (!el) return;
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    el.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
  };

  return (
    <section
      id="hero"
      style={{
        background: 'var(--navy-900)',
        color: 'var(--white)',
        // One viewport, no cropping: the orbit is height-capped (52vh inside
        // AgentSociety) so all five agents stay visible at 800–1080px heights.
        minHeight: isMobile ? 'auto' : 'calc(100dvh - 64px)',
        display: 'flex',
        alignItems: 'center',
        padding: isMobile ? 'var(--space-16) 0' : 'var(--space-8) 0',
      }}
    >
      <div
        style={{
          maxWidth: 'var(--container-xl)',
          width: '100%',
          margin: '0 auto',
          padding: '0 var(--space-6)',
          display: 'grid',
          gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr',
          gap: isMobile ? 'var(--space-12)' : 'var(--space-16)',
          alignItems: 'center',
        }}
      >
        {/* Copy column */}
        <div>
          <div style={{ marginBottom: 'var(--space-6)' }}>
            <Eyebrow tone="dark">{HACKATHON_LINE}</Eyebrow>
          </div>

          <h1
            style={{
              ...displayFont,
              fontSize: 'clamp(2.2rem, 4.2vw, 3.6rem)',
              color: 'var(--white)',
              margin: '0 0 var(--space-6)',
            }}
          >
            See applicants the way you do.
          </h1>

          <p
            style={{
              fontFamily: 'var(--font-sans)',
              fontSize: 'var(--text-lg)',
              lineHeight: 'var(--leading-relaxed)',
              color: 'var(--text-body-inverse)',
              margin: '0 0 var(--space-8)',
              maxWidth: '52ch',
            }}
          >
            A society of agents debates every inbound email against your own publications and
            capacity — and hands you a verdict with receipts.
          </p>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-3)' }}>
            <Link href={ctaHref}>
              <Button variant="accent" size="lg">{ctaLabel}</Button>
            </Link>
            <Button variant="secondary" size="lg" onClick={scrollToDemo}>
              Watch the demo
            </Button>
          </div>
        </div>

        {/* The signature: five-agent society orbiting one email */}
        <div style={{ width: '100%' }}>
          <AgentSociety />
        </div>
      </div>
    </section>
  );
}
