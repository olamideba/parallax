'use client';

export const dynamic = 'force-dynamic';

import React from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { Logo, Wordmark } from '@/components/Logo';
import { Input } from '@/components/Input';
import { Button } from '@/components/Button';
import { useIsMobile } from '@/lib/useMediaQuery';
import Link from 'next/link';

export default function SignupPage() {
  const router = useRouter();
  const isMobile = useIsMobile();
  const [displayName, setDisplayName] = React.useState('');
  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState('');
  const [success, setSuccess] = React.useState(false);

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!displayName || !email || !password) {
      setError('Please fill in all fields.');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const { data, error: authError } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            display_name: displayName,
          },
          emailRedirectTo: `${window.location.origin}/auth/callback`,
        },
      });

      if (authError) {
        setError(authError.message);
      } else {
        setSuccess(true);
        // Redirect to email verification screen after a brief delay
        setTimeout(() => {
          router.push(`/verify-email?email=${encodeURIComponent(email)}`);
        }, 1500);
      }
    } catch (err: any) {
      setError('An unexpected error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: isMobile ? 'column' : 'row', minHeight: '100vh', width: '100%' }}>
      {/* Left Column: Navy Duality Brand Panel */}
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

      {/* Right Column: Clean Ground Form Panel */}
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
          {/* Header */}
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
              Register
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
              Create your faculty account
            </h1>
            <p style={{ margin: '8px 0 0', fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>
              Set up your credentials to define your lab capacity and publications.
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSignup} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
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

            {success && (
              <div
                style={{
                  padding: '12px 14px',
                  background: 'var(--status-verified-bg)',
                  border: '1px solid var(--status-verified-ink)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--status-verified-ink)',
                  fontSize: 'var(--text-sm)',
                  fontFamily: 'var(--font-sans)',
                  lineHeight: '1.4',
                }}
              >
                Account created successfully! Redirecting to verification page...
              </div>
            )}

            <Input
              label="Full academic name"
              type="text"
              placeholder="Dr. Jane Smith"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              disabled={loading || success}
              required
            />

            <Input
              label="Academic email address"
              type="email"
              placeholder="prof@university.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading || success}
              required
            />

            <Input
              label="Password"
              type="password"
              placeholder="Min. 6 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading || success}
              required
            />

            <Button type="submit" variant="primary" fullWidth disabled={loading || success} style={{ marginTop: '8px' }}>
              {loading ? 'Creating account...' : 'Create account'}
            </Button>
          </form>

          {/* Footer Navigation */}
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
            Already have an account?{' '}
            <Link
              href="/login"
              style={{
                color: 'var(--text-accent)',
                fontWeight: 500,
                textDecoration: 'none',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.textDecoration = 'underline')}
              onMouseLeave={(e) => (e.currentTarget.style.textDecoration = 'none')}
            >
              Sign in instead
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
