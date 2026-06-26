'use client';

export const dynamic = 'force-dynamic';

import React, { Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Logo, Wordmark } from '@/components/Logo';
import { Button } from '@/components/Button';
import Link from 'next/link';

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const email = searchParams.get('email') || 'your email';

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: 'var(--surface-sunken)',
        padding: '24px',
        boxSizing: 'border-box',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '520px',
          background: 'var(--surface-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-xl)',
          boxShadow: 'var(--shadow-lg)',
          padding: '44px 40px',
          textAlign: 'center',
          boxSizing: 'border-box',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '24px',
        }}
      >
        <Logo variant="default" size={72} />
        <div>
          <Wordmark variant="default" size={18} />
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '10px',
              fontWeight: 600,
              color: 'var(--text-muted)',
              letterSpacing: 'var(--tracking-caps)',
              textTransform: 'uppercase',
              display: 'block',
              marginTop: '6px',
            }}
          >
            Verification required
          </span>
        </div>

        <h1
          style={{
            margin: '8px 0 0',
            fontFamily: 'var(--font-display)',
            fontSize: 'var(--text-display-sm)',
            fontWeight: 600,
            color: 'var(--text-strong)',
            letterSpacing: '-0.01em',
            lineHeight: 1.2,
          }}
        >
          Check your academic inbox
        </h1>

        <p
          style={{
            margin: 0,
            fontFamily: 'var(--font-sans)',
            fontSize: 'var(--text-md)',
            color: 'var(--text-body)',
            lineHeight: 'var(--leading-relaxed)',
          }}
        >
          We have sent a verification link to <strong style={{ color: 'var(--text-strong)' }}>{email}</strong>.
          Please click the link inside to verify your identity and start onboarding.
        </p>

        <div
          style={{
            background: 'var(--periwinkle-50)',
            border: '1px dashed var(--periwinkle-300)',
            borderRadius: 'var(--radius-md)',
            padding: '14px 18px',
            textAlign: 'left',
            width: '100%',
          }}
        >
          <h4
            style={{
              margin: '0 0 6px',
              fontFamily: 'var(--font-sans)',
              fontSize: 'var(--text-sm)',
              fontWeight: 600,
              color: 'var(--periwinkle-700)',
            }}
          >
            Institutional Security
          </h4>
          <p
            style={{
              margin: 0,
              fontFamily: 'var(--font-sans)',
              fontSize: 'var(--text-xs)',
              color: 'var(--text-body)',
              lineHeight: 1.4,
            }}
          >
            Parallax runs on verified faculty identifiers. If you do not see the email in a few minutes, please check your spam folder or contact your administrator.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '14px', width: '100%', marginTop: '8px' }}>
          <Button variant="secondary" fullWidth onClick={() => router.push('/login')}>
            Return to login
          </Button>
        </div>
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <div style={{ display: 'flex', minHeight: '100vh', alignItems: 'center', justifyContent: 'center', background: 'var(--surface-sunken)' }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>Loading...</span>
      </div>
    }>
      <VerifyEmailContent />
    </Suspense>
  );
}
