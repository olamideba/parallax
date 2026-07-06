'use client';

import React from 'react';
import Link from 'next/link';
import Nav from './Nav';
import Footer from './Footer';

/* Shared chrome for /privacy and /terms — the real marketing nav + footer,
   so legal pages feel like part of the same site instead of a bare template. */

export default function LegalPage({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ background: 'var(--surface-ground)', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Nav />

      <main style={{ flex: 1, padding: 'var(--space-16) var(--space-6)' }}>
        <article className="legal" style={{ maxWidth: 'var(--measure)', margin: '0 auto' }}>
          <Link
            href="/"
            style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-sm)', color: 'var(--text-accent)', textDecoration: 'none', display: 'inline-block', marginBottom: 'var(--space-8)' }}
          >
            ← Back to home
          </Link>
          {children}
        </article>
      </main>

      <Footer />
    </div>
  );
}
