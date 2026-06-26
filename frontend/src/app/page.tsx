'use client';

export const dynamic = 'force-dynamic';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { Logo, Wordmark } from '@/components/Logo';
import { Button } from '@/components/Button';
import { Loader } from 'lucide-react';

export default function Home() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    // Check initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        setUser(session.user);
        checkOnboardingAndRedirect(session.user.id);
      } else {
        router.push('/login');
      }
    });

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (session) {
        setUser(session.user);
        checkOnboardingAndRedirect(session.user.id);
      } else {
        router.push('/login');
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [router]);

  const checkOnboardingAndRedirect = (userId: string) => {
    const onboardingCompleted = localStorage.getItem(`onboarding_completed_${userId}`);
    if (onboardingCompleted === 'true') {
      // Once onboarding is completed, you go to the inbox page.
      // Since inbox/ is a separate page we will create or redirect to,
      // let's redirect to '/inbox' or show a success state.
      router.push('/inbox');
    } else {
      router.push('/onboarding');
    }
  };

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
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '20px' }}>
        <Logo size={80} />
        <Wordmark size={20} />
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '16px' }}>
          <Loader size={18} style={{ animation: 'spin 1s linear infinite', color: 'var(--text-muted)' }} />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
            AUTHENTICATING SESSION...
          </span>
        </div>
      </div>
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
