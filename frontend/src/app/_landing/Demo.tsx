'use client';

import React from 'react';
import { YOUTUBE_EMBED_ID } from './constants';
import { displayFont, Eyebrow } from './ui';

export default function Demo() {
  return (
    <section id="demo" style={{ background: 'var(--surface-ground)', padding: 'var(--space-24) var(--space-6)' }}>
      <div style={{ maxWidth: 'var(--container-lg)', margin: '0 auto', textAlign: 'center' }}>
        <Eyebrow>Demo</Eyebrow>
        <h2
          style={{
            ...displayFont,
            fontSize: 'clamp(1.6rem, 2.8vw, 2.25rem)',
            color: 'var(--text-strong)',
            margin: 'var(--space-4) 0 var(--space-3)',
          }}
        >
          See it in action
        </h2>
        <p
          style={{
            fontSize: 'var(--text-lg)',
            color: 'var(--text-muted)',
            maxWidth: '56ch',
            margin: '0 auto var(--space-10)',
          }}
        >
          A cold email lands, five agents debate it, a professor gets a grounded verdict.
        </p>

        <div
          style={{
            position: 'relative',
            aspectRatio: '16 / 9',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--border-subtle)',
            overflow: 'hidden',
            boxShadow: 'var(--shadow-lg)',
            background: 'var(--surface-sunken)',
          }}
        >
          {YOUTUBE_EMBED_ID ? (
            <iframe
              src={`https://www.youtube.com/embed/${YOUTUBE_EMBED_ID}`}
              title="Parallax demo"
              loading="lazy"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
              style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', border: 0 }}
            />
          ) : (
            <div
              style={{
                position: 'absolute',
                inset: 0,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 'var(--space-3)',
              }}
            >
              <span
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 'var(--text-xs)',
                  letterSpacing: 'var(--tracking-caps)',
                  textTransform: 'uppercase',
                  color: 'var(--text-muted)',
                }}
              >
                Demo video coming soon
              </span>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
