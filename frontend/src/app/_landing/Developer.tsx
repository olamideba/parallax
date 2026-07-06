'use client';

import React from 'react';
import { Globe, Star } from 'lucide-react';
import { GithubIcon } from './GithubIcon';
import { LinkedinIcon } from './LinkedinIcon';
import { Logo } from '@/components/Logo';
import { Button } from '@/components/Button';
import { displayFont, Eyebrow } from './ui';
import {
  DEVELOPER_NAME,
  DEVELOPER_ROLE,
  GITHUB_URL,
  LINKEDIN_URL,
  PERSONAL_SITE_URL,
} from './constants';

const LINKS = [
  { label: 'GitHub', href: GITHUB_URL, icon: GithubIcon },
  { label: 'LinkedIn', href: LINKEDIN_URL, icon: LinkedinIcon },
  { label: 'Website', href: PERSONAL_SITE_URL, icon: Globe },
];

export default function Developer() {
  return (
    <section style={{ background: 'var(--surface-sunken)', padding: 'var(--space-24) var(--space-6)' }}>
      <div
        style={{
          maxWidth: 'var(--container-md)',
          margin: '0 auto',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          gap: 'var(--space-5)',
        }}
      >
        <Eyebrow>The developer</Eyebrow>
        <h2 style={{ ...displayFont, fontSize: 'clamp(1.6rem, 2.8vw, 2.25rem)', color: 'var(--text-strong)', margin: 0 }}>
          Meet the developer
        </h2>

        <div
          style={{
            width: 96,
            height: 96,
            borderRadius: '50%',
            background: 'var(--surface-accent)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            // Brand touch: periwinkle keyline around the placeholder avatar.
            border: '2px solid var(--periwinkle-400)',
          }}
        >
          {/* Placeholder avatar until a real photo is supplied — full-color
              brand mark reads cleaner on a light disc than the mono-white one. */}
          <Logo variant="default" size={52} />
        </div>

        <div>
          <p style={{ ...displayFont, fontSize: 'var(--text-xl)', color: 'var(--text-strong)', margin: '0 0 4px' }}>
            {DEVELOPER_NAME}
          </p>
          <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)', margin: 0 }}>{DEVELOPER_ROLE}</p>
        </div>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-4)', justifyContent: 'center' }}>
          {LINKS.map(({ label, href, icon: Icon }) => (
            <a
              key={label}
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                fontFamily: 'var(--font-sans)',
                fontSize: 'var(--text-sm)',
                fontWeight: 500,
                color: 'var(--text-accent)',
                textDecoration: 'none',
              }}
            >
              <Icon size={16} /> {label}
            </a>
          ))}
        </div>

        {/* Flat-filled brand CTA, not a generic outline button. */}
        <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'none' }}>
          <Button variant="accent" leadingIcon={<Star size={15} />}>
            Star the repo
          </Button>
        </a>
      </div>
    </section>
  );
}
