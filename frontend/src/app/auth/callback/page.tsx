'use client';

export const dynamic = 'force-dynamic';

import React, { useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { Logo, Wordmark } from '@/components/Logo';
import { Loader } from '@/components/Loader';

function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = React.useState('Verifying your verification link...');
  const [errorMsg, setErrorMsg] = React.useState('');

  useEffect(() => {
    // Let the Supabase client process the code or access token in the URL automatically.
    // We listen to the auth state change to verify when the user is logged in.
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (session) {
        setStatus('Credentials verified. Entering Parallax...');
        // Clean up url queries and navigate
        setTimeout(() => {
          router.push('/onboarding');
        }, 1000);
      } else if (event === 'SIGNED_OUT') {
        setStatus('Authentication failed.');
        setErrorMsg('We could not establish a session. The verification link might be expired or invalid.');
      }
    });

    // Fallback timer if state change is slow or doesn't trigger
    const timeout = setTimeout(() => {
      supabase.auth.getSession().then(({ data: { session } }) => {
        if (session) {
          router.push('/onboarding');
        } else {
          setErrorMsg('Verification timed out. Please try logging in again.');
        }
      });
    }, 8000);

    return () => {
      subscription.unsubscribe();
      clearTimeout(timeout);
    };
  }, [router]);

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
          maxWidth: '480px',
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
        <Logo variant="default" size={64} />
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
            Securing Session
          </span>
        </div>

        {errorMsg ? (
          <>
            <h1
              style={{
                margin: 0,
                fontFamily: 'var(--font-display)',
                fontSize: 'var(--text-display-sm)',
                fontWeight: 600,
                color: 'var(--status-refuted-ink)',
                letterSpacing: '-0.01em',
              }}
            >
              Verification Failed
            </h1>
            <p
              style={{
                margin: 0,
                fontFamily: 'var(--font-sans)',
                fontSize: 'var(--text-sm)',
                color: 'var(--text-body)',
                lineHeight: 1.5,
              }}
            >
              {errorMsg}
            </p>
            <a
              href="/login"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: 'var(--control-md)',
                padding: '0 16px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--action)',
                color: 'var(--action-text)',
                fontFamily: 'var(--font-sans)',
                fontWeight: 500,
                fontSize: 'var(--text-sm)',
                textDecoration: 'none',
                width: '100%',
                marginTop: '12px',
              }}
            >
              Back to Sign In
            </a>
          </>
        ) : (
          <>
            <div
              style={{
                width: '28px',
                height: '28px',
                border: '2px solid var(--periwinkle-200)',
                borderTopColor: 'var(--accent)',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite',
              }}
            />
            <p
              style={{
                margin: 0,
                fontFamily: 'var(--font-mono)',
                fontSize: 'var(--text-xs)',
                color: 'var(--text-muted)',
                letterSpacing: '0.02em',
              }}
            >
              {status}
            </p>
            <style>{`
              @keyframes spin {
                to { transform: rotate(360deg); }
              }
            `}</style>
          </>
        )}
      </div>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={
      <Loader fullscreen width={160} label="Loading..." />
    }>
      <AuthCallbackContent />
    </Suspense>
  );
}
