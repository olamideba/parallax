'use client';

export const dynamic = 'force-dynamic';

import React from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { api } from '@/lib/api';
import { Logo, Wordmark } from '@/components/Logo';
import { Input } from '@/components/Input';
import { Button } from '@/components/Button';
import { useIsMobile } from '@/lib/useMediaQuery';
import Link from 'next/link';

export default function LoginPage() {
  const router = useRouter();
  const isMobile = useIsMobile();
  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please enter both email and password.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const { data, error: authError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (authError) {
        setError(authError.message);
        setLoading(false);
        return;
      }
      if (data?.user) {
        // Onboarding completion is a backend fact (has the professor actually
        // set up lab capacity?), not a per-browser localStorage flag — that
        // flag is unset on any new device/browser/incognito session, which
        // was sending already-onboarded professors back into the wizard on
        // every login. Treat "capacity or topics declared" as done.
        try {
          const prof = await api.getProfessorProfile();
          const hasOnboarded = prof.open_slots > 0 || prof.recruiting_topics.length > 0;
          router.push(hasOnboarded ? '/inbox' : '/onboarding');
        } catch {
          // Profile fetch failed — fall back to onboarding rather than
          // stranding the user on the login page.
          router.push('/onboarding');
        }
      }
    } catch (err: any) {
      setError('An unexpected error occurred. Please try again.');
      setLoading(false);
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
          {!isMobile && (
            <p
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: 'var(--text-lg)',
                fontStyle: 'italic',
                fontWeight: 300,
                color: 'var(--text-body-inverse)',
                lineHeight: 'var(--leading-relaxed)',
                marginTop: '16px',
              }}
            >
              "A society of agents, debating candidate outreach against the ground truth of your research and capacity."
            </p>
          )}
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
              Sign In
            </span>
            <h1
              style={{
                margin: 0,
                fontFamily: 'var(--font-display)',
                fontSize: 'var(--text-display-sm)',
                fontWeight: 600,
                color: 'var(--text-strong)',
                letterSpacing: '-0.01em',
              }}
            >
              Access your review board
            </h1>
            <p style={{ margin: '8px 0 0', fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>
              Enter your academic credentials to view inbound outreaches.
            </p>
          </div>

          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
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

            <div>
              <Input
                label="Password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                required
              />
              <div style={{ textAlign: 'right', marginTop: '8px' }}>
                <Link
                  href="/forgot-password"
                  style={{ fontSize: 'var(--text-xs)', color: 'var(--text-accent)', fontWeight: 500, textDecoration: 'none' }}
                  onMouseEnter={(e) => (e.currentTarget.style.textDecoration = 'underline')}
                  onMouseLeave={(e) => (e.currentTarget.style.textDecoration = 'none')}
                >
                  Forgot password?
                </Link>
              </div>
            </div>

            <Button type="submit" variant="primary" fullWidth disabled={loading} style={{ marginTop: '8px' }}>
              {loading ? 'Verifying...' : 'Sign in'}
            </Button>
          </form>

          <div
            style={{
              marginTop: '32px',
              borderTop: '1px solid var(--border-subtle)',
              paddingTop: '20px',
              textAlign: 'center',
              fontSize: 'var(--text-sm)',
              color: 'var(--text-muted)',
            }}
          >
            New to Parallax?{' '}
            <Link
              href="/signup"
              style={{
                color: 'var(--text-accent)',
                fontWeight: 500,
                textDecoration: 'none',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.textDecoration = 'underline')}
              onMouseLeave={(e) => (e.currentTarget.style.textDecoration = 'none')}
            >
              Create an account
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
