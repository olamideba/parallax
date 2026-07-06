import React from 'react';
import type { Metadata } from 'next';
import LegalPage from '../_landing/LegalPage';
import { CONTACT_EMAIL } from '../_landing/constants';

export const metadata: Metadata = {
  title: 'Privacy — Parallax',
  description: 'What data the Parallax hackathon demo touches and why.',
};

const h2: React.CSSProperties = { fontFamily: 'var(--font-display)', fontSize: 'var(--text-xl)', color: 'var(--text-strong)', margin: 'var(--space-8) 0 var(--space-3)' };
const p: React.CSSProperties = { fontSize: 'var(--text-md)', lineHeight: 'var(--leading-relaxed)', color: 'var(--text-body)', margin: '0 0 var(--space-4)' };
const li: React.CSSProperties = { fontSize: 'var(--text-md)', lineHeight: 'var(--leading-relaxed)', color: 'var(--text-body)', margin: '0 0 var(--space-3)' };

export default function PrivacyPage() {
  return (
    <LegalPage>
      <h1 style={{ marginBottom: 'var(--space-2)' }}>Privacy</h1>
      <p style={{ ...p, color: 'var(--text-muted)', fontSize: 'var(--text-sm)' }}>Hackathon demo</p>

      <p style={p}>
        Parallax is a project built for the Global AI Hackathon Series with Qwen Cloud. This page
        explains, in plain language, what data the demo touches and why.
      </p>

      <h2 style={h2}>What we collect</h2>
      <ul style={{ paddingLeft: 'var(--space-6)', margin: '0 0 var(--space-4)' }}>
        <li style={li}>
          <strong>Professor accounts:</strong> name, email, and password, via Supabase Auth, when
          you sign up.
        </li>
        <li style={li}>
          <strong>Publications you connect:</strong> DOIs, ORCID data, or PDFs you upload, used only
          to ground the AI agents&apos; evaluation of incoming students.
        </li>
        <li style={li}>
          <strong>Lab profile:</strong> the recruiting topics, open slots, and funding context you
          enter.
        </li>
        <li style={li}>
          <strong>Inbound candidate email:</strong> messages sent to your unique Parallax intake
          address are received, read by the AI agent pipeline, and may trigger an automated reply
          sent from your address. Prospective students don&apos;t sign up for Parallax directly — if
          they email a professor&apos;s intake address, their message content is processed the same
          way, for the sole purpose of generating a triage decision for that professor.
        </li>
      </ul>

      <h2 style={h2}>How it&apos;s used</h2>
      <p style={p}>
        Solely to run the triage and debate pipeline and produce a decision for the professor to
        review. Not sold, not used for advertising, not shared beyond the infrastructure providers
        required to run the demo (Supabase, Cloudflare R2, Redis Cloud, Alibaba Cloud, and Qwen for
        inference).
      </p>

      <h2 style={h2}>Retention</h2>
      <p style={p}>
        Data is kept only for the duration of the hackathon evaluation period. You can request
        deletion of your account and associated data at any time.
      </p>

      <h2 style={h2}>Contact</h2>
      <p style={p}>{CONTACT_EMAIL} for any data questions or deletion requests.</p>
    </LegalPage>
  );
}
