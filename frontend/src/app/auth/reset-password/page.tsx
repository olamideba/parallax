'use client';

export const dynamic = 'force-dynamic';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { Logo, Wordmark } from '@/components/Logo';
import { Input } from '@/components/Input';
import { Button } from '@/components/Button';
import { Loader } from '@/components/Loader';
import { useIsMobile } from '@/lib/useMediaQuery';
import Link from 'next/link';
import { CheckCircle } from 'lucide-react';

export default function ResetPasswordPage() {
  const router = useRouter();
  const isMobile = useIsMobile();

  // Supabase's recovery link exchanges its token for a session automatically
  // and fires a PASSWORD_RECOVERY event — we gate the form on that instead of
  // just "is there a session", since a normal logged-in visit to this URL
  // shouldn't be treated as a valid recovery flow.
  const [ready, setReady] = useState(false);
  const [linkError, setLinkError] = useState(false);

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event) => {
      if (event === 'PASSWORD_RECOVERY') {
        setReady(true);
      }
    });

    // If Supabase already processed the recovery token before this listener
    // attached (e.g. fast redirect), a session will exist — accept that too.
    const timeout = setTimeout(() => {
      supabase.auth.getSession().then(({ data: { session } }) => {
        if (session) {
          setReady(true);
        } else {
          setLinkError(true);
        }
      });
    }, 2500);

    return () => {
      subscription.unsubscribe();
      clearTimeout(timeout);
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    setError('');

    const { error: authError } = await supabase.auth.updateUser({ password });

    setLoading(false);

    if (authError) {
      setError(authError.message);
    } else {
      setDone(true);
      setTimeout(() => router.push('/inbox'), 2000);
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
          <Wordmark variant="inverse" size={isMobile ? 20 : 24} />
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
          {!ready && !linkError ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
              <Loader width={140} />
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
                VERIFYING RESET LINK...
              </span>
            </div>
          ) : linkError ? (
            <>
              <h1
                style={{
                  margin: '0 0 8px',
                  fontFamily: 'var(--font-display)',
                  fontSize: 'var(--text-display-sm)',
                  fontWeight: 700,
                  color: 'var(--status-refuted-ink)',
                  letterSpacing: '-0.01em',
                }}
              >
                Link expired or invalid
              </h1>
              <p style={{ margin: '0 0 24px', fontSize: 'var(--text-sm)', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                This password reset link is no longer valid. Request a new one to continue.
              </p>
              <Link href="/forgot-password" style={{ textDecoration: 'none' }}>
                <Button variant="primary" fullWidth>Request a new link</Button>
              </Link>
            </>
          ) : done ? (
            <>
              <div
                style={{
                  width: 44, height: 44, borderRadius: '999px',
                  background: 'var(--status-verified-bg)', color: 'var(--status-verified-ink)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '20px',
                }}
              >
                <CheckCircle size={20} />
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
                Password updated
              </h1>
              <p style={{ margin: 0, fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>
                Taking you to your inbox...
              </p>
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
                  Set a new password
                </h1>
                <p style={{ margin: '8px 0 0', fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>
                  Choose a new password for your account.
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
                  label="New password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={loading}
                  hint="At least 8 characters."
                  required
                />

                <Input
                  label="Confirm new password"
                  type="password"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  disabled={loading}
                  required
                />

                <Button type="submit" variant="primary" fullWidth disabled={loading} style={{ marginTop: '8px' }}>
                  {loading ? 'Updating...' : 'Update password'}
                </Button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
