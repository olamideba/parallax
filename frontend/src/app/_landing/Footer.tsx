'use client';

import React from 'react';
import Link from 'next/link';
import { GithubIcon } from './GithubIcon';
import { Logo, Wordmark } from '@/components/Logo';
import { GITHUB_URL, HACKATHON_LINE } from './constants';

const anchorScroll = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
  e.preventDefault();
  const el = document.querySelector(href);
  if (el) {
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    el.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
  }
};

const colLabel: React.CSSProperties = {
  // Panchang column labels — same display face as every other heading.
  fontFamily: 'var(--font-brand)',
  fontWeight: 700,
  fontSize: 'var(--text-2xs)',
  letterSpacing: 'var(--tracking-caps)',
  textTransform: 'uppercase',
  color: 'var(--periwinkle-300)',
  margin: '0 0 var(--space-4)',
};

const linkStyle: React.CSSProperties = {
  fontFamily: 'var(--font-sans)',
  fontSize: 'var(--text-sm)',
  color: 'var(--text-body-inverse)',
  textDecoration: 'none',
  display: 'inline-flex',
  alignItems: 'center',
  gap: 6,
};

export default function Footer() {
  return (
    <footer style={{ background: 'var(--navy-950)', color: 'var(--white)', padding: 'var(--space-16) var(--space-6) var(--space-10)' }}>
      <div style={{ maxWidth: 'var(--container-xl)', margin: '0 auto' }}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
            gap: 'var(--space-10)',
            paddingBottom: 'var(--space-10)',
            // Brand touch: periwinkle hairline instead of a default gray rule.
            borderBottom: '1px solid var(--periwinkle-600)',
          }}
        >
          <div>
            <Link href="/" style={{ display: 'inline-flex', alignItems: 'center', gap: 10, textDecoration: 'none', marginBottom: 'var(--space-4)' }}>
              <Logo variant="on-dark" size={26} />
              <Wordmark variant="inverse" size={16} />
            </Link>
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-2xs)', color: 'var(--text-muted-inverse)', lineHeight: 1.5, maxWidth: 260, letterSpacing: '0.04em' }}>
              {HACKATHON_LINE}
            </p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <p style={colLabel}>Product</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              <a href="#demo" onClick={(e) => anchorScroll(e, '#demo')} style={linkStyle}>Demo</a>
              <a href="#how-it-works" onClick={(e) => anchorScroll(e, '#how-it-works')} style={linkStyle}>How it Works</a>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <p style={colLabel}>Legal</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              <Link href="/privacy" style={linkStyle}>Privacy</Link>
              <Link href="/terms" style={linkStyle}>Terms</Link>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <p style={colLabel}>Connect</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer" aria-label="GitHub repository" style={linkStyle}>
                <GithubIcon size={16} /> GitHub
              </a>
            </div>
          </div>
        </div>

        <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted-inverse)', margin: 'var(--space-6) 0 0' }}>
          © {new Date().getFullYear()} Parallax
        </p>
      </div>
    </footer>
  );
}
