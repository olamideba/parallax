'use client';

import React from 'react';
import Link from 'next/link';
import { Menu, X } from 'lucide-react';
import { GithubIcon } from './GithubIcon';
import { Logo, Wordmark } from '@/components/Logo';
import { Button } from '@/components/Button';
import { useIsMobile } from '@/lib/useMediaQuery';
import { GITHUB_URL } from './constants';

const LINKS = [
  { label: 'Demo', href: '#demo' },
  { label: 'Why Parallax', href: '#problem' },
  { label: 'How it Works', href: '#how-it-works' },
];

export default function Nav({ authed = false }: { authed?: boolean }) {
  const isMobile = useIsMobile();
  const [scrolled, setScrolled] = React.useState(false);
  const [open, setOpen] = React.useState(false);
  const ctaHref = authed ? '/inbox' : '/signup';
  const ctaLabel = authed ? 'Go to inbox' : 'Try it free';

  React.useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // The nav is always a solid white surface (navy logo + gray links) — cleaner
  // than alternating navy↔white. Scroll only deepens the elevation: a hairline
  // border + subtle shadow appear once the page moves.
  const linkColor = 'var(--text-body)';

  const linkStyle: React.CSSProperties = {
    fontFamily: 'var(--font-sans)',
    fontSize: 'var(--text-sm)',
    color: linkColor,
    textDecoration: 'none',
    fontWeight: 500,
  };

  const handleAnchor = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    if (!href.startsWith('#')) return;
    e.preventDefault();
    setOpen(false);
    const el = document.querySelector(href);
    if (el) {
      const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      el.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
    }
  };

  return (
    <header
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 'var(--z-sticky)' as React.CSSProperties['zIndex'],
        background: 'var(--surface-ground)',
        borderBottom: scrolled ? '1px solid var(--border-subtle)' : '1px solid transparent',
        boxShadow: scrolled ? 'var(--shadow-sm)' : 'none',
        transition: 'border-color var(--duration-normal) var(--ease-standard), box-shadow var(--duration-normal) var(--ease-standard)',
      }}
    >
      <nav
        style={{
          maxWidth: 'var(--container-xl)',
          margin: '0 auto',
          padding: '0 var(--space-6)',
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 'var(--space-6)',
        }}
      >
        <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none', flexShrink: 0 }}>
          <Logo variant="default" size={28} />
          <Wordmark variant="default" size={16} />
        </Link>

        {!isMobile && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-6)' }}>
            {LINKS.map((l) => (
              <a key={l.href} href={l.href} style={linkStyle} onClick={(e) => handleAnchor(e, l.href)}>
                {l.label}
              </a>
            ))}
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="GitHub repository"
              style={{ display: 'inline-flex', color: linkColor, transition: 'color var(--duration-fast) var(--ease-standard)' }}
            >
              <GithubIcon size={20} />
            </a>
            <Link href={ctaHref}>
              <Button variant="primary" size="sm">{ctaLabel}</Button>
            </Link>
          </div>
        )}

        {isMobile && (
          <button
            type="button"
            aria-label={open ? 'Close menu' : 'Open menu'}
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
            style={{
              display: 'inline-flex',
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-strong)',
              padding: 8,
            }}
          >
            {open ? <X size={24} /> : <Menu size={24} />}
          </button>
        )}
      </nav>

      {isMobile && open && (
        <div
          style={{
            background: 'var(--surface-ground)',
            borderTop: '1px solid var(--border-subtle)',
            padding: 'var(--space-4) var(--space-6) var(--space-6)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-4)',
          }}
        >
          {LINKS.map((l) => (
            <a
              key={l.href}
              href={l.href}
              onClick={(e) => handleAnchor(e, l.href)}
              style={{ ...linkStyle, color: 'var(--text-body)', fontSize: 'var(--text-md)' }}
            >
              {l.label}
            </a>
          ))}
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="GitHub repository"
            style={{ display: 'inline-flex', alignItems: 'center', gap: 8, color: 'var(--text-body)', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-md)', fontWeight: 500, textDecoration: 'none' }}
          >
            <GithubIcon size={18} /> GitHub
          </a>
          <Link href={ctaHref} style={{ marginTop: 4 }}>
            <Button variant="primary" fullWidth>{ctaLabel}</Button>
          </Link>
        </div>
      )}
    </header>
  );
}
