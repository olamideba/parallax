'use client';

export const dynamic = 'force-dynamic';

import React, { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import { Wordmark } from '@/components/Logo';
import { Loader } from '@/components/Loader';
import LandingPage from './_landing/LandingPage';

export default function Home() {
  const [checking, setChecking] = useState(true);
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    // The root route is the marketing landing for everyone. We don't redirect
    // authenticated professors away — instead the landing's CTAs adapt (a
    // signed-in user sees "Go to inbox" rather than "Try it free"). We only
    // resolve the session so those CTAs render correctly.
    supabase.auth.getSession().then(({ data: { session } }) => {
      setAuthed(!!session);
      setChecking(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      setAuthed(!!session);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  // Brief loader while the initial session check resolves — avoids a flash of
  // the logged-out CTAs before we know the user is signed in.
  if (checking) {
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
          <Loader width={200} />
          <Wordmark size={20} />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
            LOADING...
          </span>
        </div>
      </div>
    );
  }

  return <LandingPage authed={authed} />;
}
