'use client';

export const dynamic = 'force-dynamic';

import React from 'react';
import { supabase } from '@/lib/supabase';
import { Logo, Wordmark } from '@/components/Logo';
import { Input } from '@/components/Input';
import { Button } from '@/components/Button';
import { useIsMobile } from '@/lib/useMediaQuery';
import Link from 'next/link';
import { ArrowLeft, MailCheck } from 'lucide-react';

export default function ForgotPasswordPage() {
  const isMobile = useIsMobile();
  const [email, setEmail] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState('');
  const [sent, setSent] = React.useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setError('Please enter your email address.');
      return;
    }

    setLoading(true);
    setError('');

    const { error: authError } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/auth/reset-password`,
    });

    setLoading(false);

    // Always show the same success state regardless of whether the email
    // exists — otherwise this becomes an account-enumeration oracle.
    if (authError && authError.status && authError.status >= 500) {
      setError('Something went wrong sending the reset link. Please try again.');
    } else {
      setSent(true);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: isMobile ? 'column' : 'row', minHeight: '100vh', width: '100%' }}>
      <div
        style={{
          flex: isMobile ? 'none' : 1,
          background: 'var(--navy-900)',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          padding: isMobile ? '28px 24px' : '40px',
          color: 'var(--white)',
          textAlign: 'center',
          borderRight: isMobile ? 'none' : '1px solid var(--border-inverse)',
          borderBottom: isMobile ? '1px solid var(--border-inverse)' : 'none',
        }}
      >
        <div style={{ maxWidth: '460px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: isMobile ? '14px' : '28px' }}>
          <Logo variant="on-dark" size={isMobile ? 56 : 120} />
          <div>
            <Wordmark variant="inverse" size={isMobile ? 20 : 24} />
            <p
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
                color: 'var(--periwinkle-300)',
                letterSpacing: '0.18em',
                marginTop: '12px',
                textTransform: 'uppercase',
              }}
            >
              Graduate admissions review
            </p>
          </div>
        </div>
      </div>

      <div
        style={{
          flex: 1,
          background: 'var(--surface-ground)',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          padding: isMobile ? '40px 24px' : '40px',
        }}
      >
        <div style={{ width: '100%', maxWidth: '400px' }}>
          {sent ? (
            <>
              <div
                style={{
                  width: 44, height: 44, borderRadius: '999px',
                  background: 'var(--status-verified-bg)', color: 'var(--status-verified-ink)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '20px',
                }}
              >
                <MailCheck size={20} />
              </div>
              <h1
                style={{
                  margin: '0 0 8px',
                  fontFamily: 'var(--font-display)',
                  fontSize: 'var(--text-display-sm)',
                  fontWeight: 700,
                  color: 'var(--text-strong)',
                  letterSpacing: '-0.01em',
                }}
              >
                Check your inbox
              </h1>
              <p style={{ margin: '0 0 28px', fontSize: 'var(--text-sm)', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                If an account exists for <strong style={{ color: 'var(--text-body)' }}>{email}</strong>, we&apos;ve sent a link to reset the password. It expires shortly, so use it soon.
              </p>
              <Link href="/login" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', textDecoration: 'none', color: 'var(--text-accent)', fontWeight: 500, fontSize: 'var(--text-sm)' }}>
                <ArrowLeft size={15} />
                Back to sign in
              </Link>
            </>
          ) : (
            <>
              <div style={{ marginBottom: '32px' }}>
                <span
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '10px',
                    fontWeight: 600,
                    color: 'var(--text-muted)',
                    letterSpacing: 'var(--tracking-caps)',
                    textTransform: 'uppercase',
                    display: 'block',
                    marginBottom: '6px',
                  }}
                >
                  Reset password
                </span>
                <h1
                  style={{
                    margin: 0,
                    fontFamily: 'var(--font-display)',
                    fontSize: 'var(--text-display-sm)',
                    fontWeight: 700,
                    color: 'var(--text-strong)',
                    letterSpacing: '-0.01em',
                  }}
                >
                  Forgot your password?
                </h1>
                <p style={{ margin: '8px 0 0', fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>
                  Enter your account email and we&apos;ll send you a link to set a new one.
                </p>
              </div>

              <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                {error && (
                  <div
                    style={{
                      padding: '12px 14px',
                      background: 'var(--status-refuted-bg)',
                      border: '1px solid var(--status-refuted-ink)',
                      borderRadius: 'var(--radius-md)',
                      color: 'var(--status-refuted-ink)',
                      fontSize: 'var(--text-sm)',
                      fontFamily: 'var(--font-sans)',
                      lineHeight: '1.4',
                    }}
                  >
                    {error}
                  </div>
                )}

                <Input
                  label="Email address"
                  type="email"
                  placeholder="prof@university.edu"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={loading}
                  required
                />

                <Button type="submit" variant="primary" fullWidth disabled={loading} style={{ marginTop: '8px' }}>
                  {loading ? 'Sending link...' : 'Send reset link'}
                </Button>
              </form>

              <div style={{ marginTop: '32px', borderTop: '1px solid var(--border-subtle)', paddingTop: '20px', textAlign: 'center' }}>
                <Link
                  href="/login"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', textDecoration: 'none', color: 'var(--text-muted)', fontSize: 'var(--text-sm)' }}
                >
                  <ArrowLeft size={15} />
                  Back to sign in
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
