import React from 'react';
import type { Metadata } from 'next';
import LegalPage from '../_landing/LegalPage';
import { CONTACT_EMAIL } from '../_landing/constants';

export const metadata: Metadata = {
  title: 'Terms of Use — Parallax',
  description: 'Terms for the Parallax hackathon demo.',
};

const p: React.CSSProperties = { fontSize: 'var(--text-md)', lineHeight: 'var(--leading-relaxed)', color: 'var(--text-body)', margin: '0 0 var(--space-4)' };
const li: React.CSSProperties = { fontSize: 'var(--text-md)', lineHeight: 'var(--leading-relaxed)', color: 'var(--text-body)', margin: '0 0 var(--space-3)' };

export default function TermsPage() {
  return (
    <LegalPage>
      <h1 style={{ marginBottom: 'var(--space-2)' }}>Terms of Use</h1>
      <p style={{ ...p, color: 'var(--text-muted)', fontSize: 'var(--text-sm)' }}>Hackathon demo</p>

      <p style={p}>
        Parallax is an early-stage hackathon prototype, not a production service, offered as-is for
        evaluation purposes.
      </p>

      <ul style={{ paddingLeft: 'var(--space-6)', margin: '0 0 var(--space-4)' }}>
        <li style={li}>
          Triage verdicts are AI-generated and should be treated as a decision aid, not a final
          admissions decision.
        </li>
        <li style={li}>
          The software is provided &ldquo;as is,&rdquo; with no warranty or uptime guarantee, during the
          hackathon evaluation period.
        </li>
        <li style={li}>
          Don&apos;t use the intake pipeline to send spam, malicious content, or attempt to abuse the
          system.
        </li>
        <li style={li}>This demo may be modified or taken offline at any time without notice.</li>
        <li style={li}>Contact: {CONTACT_EMAIL}</li>
      </ul>
    </LegalPage>
  );
}
