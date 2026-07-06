'use client';

import React from 'react';
import { ShieldCheck, BookOpen, Stamp, Coins, Scale } from 'lucide-react';
import { useIsMobile } from '@/lib/useMediaQuery';
import { displayFont, Eyebrow, DashedConnector } from './ui';

interface AgentCard {
  name: string;
  desc: string;
  icon: React.ComponentType<{ size?: number; strokeWidth?: number; color?: string }>;
  color: string;
  ink: string;
  bg: string;
}

const GATEKEEPER: AgentCard = {
  name: 'Gatekeeper',
  desc: 'Fast, cheap pre-filter. Kills obvious mass-mail and spam before anything expensive runs.',
  icon: ShieldCheck,
  color: 'var(--gray-500)',
  ink: 'var(--gray-700)',
  bg: 'var(--gray-100)',
};

const DEBATERS: AgentCard[] = [
  {
    name: 'Research-Fit Advocate',
    desc: "Argues for the candidate: does their stated interest actually match the professor's published work?",
    icon: BookOpen,
    color: 'var(--agent-1)',
    ink: 'var(--agent-1-ink)',
    bg: 'var(--agent-1-bg)',
  },
  {
    name: 'Authenticity Auditor',
    desc: 'Checks whether the candidate’s claims hold up — real publications, real credentials, real specificity.',
    icon: Stamp,
    color: 'var(--agent-2)',
    ink: 'var(--agent-2-ink)',
    bg: 'var(--agent-2-bg)',
  },
  {
    name: 'Capacity & Funding Assessor',
    desc: 'Weighs the professor’s actual open slots and funding against what the candidate needs.',
    icon: Coins,
    color: 'var(--agent-3)',
    ink: 'var(--agent-3-ink)',
    bg: 'var(--agent-3-bg)',
  },
];

const ARBITRATOR: AgentCard = {
  name: 'Arbitrator',
  desc: 'Reads the full debate and returns one grounded verdict, with the evidence attached.',
  icon: Scale,
  color: 'var(--agent-4)',
  ink: 'var(--agent-4-ink)',
  bg: 'var(--agent-4-bg)',
};

const TECH = ['Alibaba Cloud ECS', 'Next.js', 'FastAPI', 'Celery', 'PostgreSQL', 'Qwen / DashScope', 'Cloudflare R2', 'Redis', 'Tailscale'];

function Card({ card, wide }: { card: AgentCard; wide?: boolean }) {
  const Icon = card.icon;
  const [hover, setHover] = React.useState(false);
  return (
    <div
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        background: card.bg,
        border: `1px solid ${card.color}`,
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-5)',
        width: '100%',
        maxWidth: wide ? 440 : undefined,
        transform: hover ? 'translateY(-3px)' : 'translateY(0)',
        boxShadow: hover ? 'var(--shadow-md)' : 'none',
        transition: 'transform var(--duration-normal) var(--ease-out), box-shadow var(--duration-normal) var(--ease-out)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 'var(--space-3)' }}>
        <span
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 34,
            height: 34,
            borderRadius: '50%',
            background: card.color,
            flexShrink: 0,
          }}
        >
          <Icon size={17} strokeWidth={2} color="#FEFEFE" />
        </span>
        <h3 style={{ ...displayFont, fontSize: 'var(--text-md)', color: card.ink, margin: 0 }}>{card.name}</h3>
      </div>
      <p style={{ fontSize: 'var(--text-sm)', lineHeight: 'var(--leading-normal)', color: 'var(--text-body)', margin: 0 }}>
        {card.desc}
      </p>
    </div>
  );
}

export default function HowItWorks() {
  const isMobile = useIsMobile();

  return (
    <section id="how-it-works" style={{ background: 'var(--surface-ground)', padding: 'var(--space-24) var(--space-6)' }}>
      <div style={{ maxWidth: 'var(--container-lg)', margin: '0 auto', textAlign: 'center' }}>
        <Eyebrow>How it works</Eyebrow>
        <h2 style={{ ...displayFont, fontSize: 'clamp(1.6rem, 2.8vw, 2.25rem)', color: 'var(--text-strong)', margin: 'var(--space-4) 0 var(--space-3)' }}>
          Five agents, one debate, per email.
        </h2>
        <p style={{ fontSize: 'var(--text-lg)', color: 'var(--text-muted)', margin: '0 0 var(--space-12)' }}>
          The same society you saw above — here&apos;s the order they work in.
        </p>

        {/* Flow: Gatekeeper → (3 debaters) → Arbitrator, joined by the same
            dashed-line language as the hero orbit. */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'left' }}>
          <Card card={GATEKEEPER} wide />
          <DashedConnector />
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)',
              gap: 'var(--space-4)',
              width: '100%',
            }}
          >
            {DEBATERS.map((d) => (
              <Card key={d.name} card={d} />
            ))}
          </div>
          <DashedConnector />
          <Card card={ARBITRATOR} wide />
        </div>

        {/* Tech stack strip */}
        <div style={{ marginTop: 'var(--space-16)' }}>
          <p
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 'var(--text-2xs)',
              letterSpacing: 'var(--tracking-caps)',
              textTransform: 'uppercase',
              color: 'var(--text-subtle)',
              margin: '0 0 var(--space-4)',
            }}
          >
            Built on
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)', justifyContent: 'center' }}>
            {TECH.map((t) => (
              <span
                key={t}
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 'var(--text-xs)',
                  color: 'var(--text-body)',
                  background: 'var(--surface-muted)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '5px 10px',
                }}
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
