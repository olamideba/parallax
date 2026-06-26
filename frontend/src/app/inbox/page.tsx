'use client';

export const dynamic = 'force-dynamic';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { Logo, Wordmark } from '@/components/Logo';
import { Button } from '@/components/Button';
import { Tag } from '@/components/Tag';
import { Inbox, LogOut, Users, BookOpen, Settings } from 'lucide-react';

export default function InboxPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [displayName, setDisplayName] = useState('');
  const [slots, setSlots] = useState('0');
  const [committed, setCommitted] = useState('0');
  const [areas, setAreas] = useState<string[]>([]);
  const [funding, setFunding] = useState('');

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        setUser(session.user);
        setDisplayName(session.user.user_metadata?.display_name || 'Dr. Professor');
        loadLabSettings(session.user.id);
      } else {
        router.push('/login');
      }
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (session) {
        setUser(session.user);
        setDisplayName(session.user.user_metadata?.display_name || 'Dr. Professor');
        loadLabSettings(session.user.id);
      } else {
        router.push('/login');
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [router]);

  const loadLabSettings = (userId: string) => {
    const savedSlots = localStorage.getItem(`lab_slots_${userId}`) || '3';
    const savedCommitted = localStorage.getItem(`lab_committed_${userId}`) || '1';
    const savedFunding = localStorage.getItem(`lab_funding_${userId}`) || '';
    const savedAreas = localStorage.getItem(`lab_areas_${userId}`);

    setSlots(savedSlots);
    setCommitted(savedCommitted);
    setFunding(savedFunding);
    if (savedAreas) {
      try {
        setAreas(JSON.parse(savedAreas));
      } catch (e) {
        setAreas([]);
      }
    } else {
      setAreas(['Sparse attention', 'Long-context retrieval', 'Efficient transformers']);
    }
  };

  const handleSignout = async () => {
    await supabase.auth.signOut();
    router.push('/login');
  };

  const handleResetOnboarding = () => {
    if (user) {
      localStorage.removeItem(`onboarding_completed_${user.id}`);
      router.push('/onboarding');
    }
  };

  const effectiveSlots = Math.max(0, parseInt(slots) - parseInt(committed));

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--surface-sunken)' }}>
      {/* Top Header */}
      <header style={{ borderBottom: '1px solid var(--border-subtle)', background: 'var(--surface-card)' }}>
        <div style={{ maxWidth: '1120px', margin: '0 auto', padding: '18px 24px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              width: 30, height: 30, borderRadius: '7px',
              background: '#FEFEFE',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0, boxShadow: '0 1px 3px rgba(0,0,0,0.12)',
            }}
          >
            <Logo size={22} />
          </div>
          <Wordmark size={18} />
          <span style={{ flex: 1 }} />
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <span style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', color: 'var(--text-strong)', fontWeight: 500 }}>
              {displayName}
            </span>
            <button
              onClick={handleSignout}
              title="Sign out"
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                padding: '6px',
                borderRadius: 'var(--radius-sm)',
                transition: 'background var(--duration-fast)',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--surface-muted)')}
              onMouseLeave={(e) => (e.currentTarget.style.background = 'none')}
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main
        style={{
          flex: 1,
          width: '100%',
          maxWidth: '1120px',
          margin: '0 auto',
          padding: '44px 24px 80px',
          display: 'grid',
          gridTemplateColumns: '1fr 300px',
          gap: '32px',
          boxSizing: 'border-box',
        }}
      >
        {/* Left Side: Inbox review queue */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div>
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
              Review queue
            </span>
            <h1
              style={{
                margin: 0,
                fontFamily: 'var(--font-display)',
                fontSize: 'var(--text-display-md)',
                fontWeight: 600,
                color: 'var(--text-strong)',
                letterSpacing: '-0.01em',
              }}
            >
              Candidate outreach
            </h1>
          </div>

          {/* Tabs */}
          <div
            style={{
              display: 'flex',
              borderBottom: '1px solid var(--border-subtle)',
              gap: '24px',
              paddingBottom: '1px',
            }}
          >
            {['Pending review', 'Auto-resolved', 'Declined'].map((tab, idx) => (
              <span
                key={tab}
                style={{
                  fontFamily: 'var(--font-sans)',
                  fontSize: 'var(--text-sm)',
                  fontWeight: idx === 0 ? 600 : 500,
                  color: idx === 0 ? 'var(--text-strong)' : 'var(--text-muted)',
                  borderBottom: idx === 0 ? '2px solid var(--navy-900)' : 'none',
                  paddingBottom: '10px',
                  cursor: 'pointer',
                }}
              >
                {tab}
              </span>
            ))}
          </div>

          {/* Empty state card */}
          <div
            style={{
              background: 'var(--surface-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-xl)',
              boxShadow: 'var(--shadow-sm)',
              padding: '60px 40px',
              textAlign: 'center',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '16px',
            }}
          >
            <div
              style={{
                width: '44px',
                height: '44px',
                borderRadius: '50%',
                background: 'var(--gray-50)',
                border: '1px solid var(--border-subtle)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--text-subtle)',
              }}
            >
              <Inbox size={20} />
            </div>
            <p
              style={{
                margin: 0,
                fontFamily: 'var(--font-sans)',
                fontSize: 'var(--text-md)',
                color: 'var(--text-body)',
                fontWeight: 500,
              }}
            >
              No items pending review.
            </p>
            <p
              style={{
                margin: 0,
                fontFamily: 'var(--font-sans)',
                fontSize: 'var(--text-sm)',
                color: 'var(--text-muted)',
                maxWidth: '36ch',
                lineHeight: 'var(--leading-normal)',
              }}
            >
              When prospective students email you, the debate society will triages them here.
            </p>
          </div>
        </div>

        {/* Right Side: Lab Profile Card summary */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div
            style={{
              background: 'var(--surface-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-xl)',
              boxShadow: 'var(--shadow-sm)',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '20px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ color: 'var(--navy-900)' }}>
                <Users size={18} />
              </div>
              <h3 style={{ margin: 0, fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', fontWeight: 600 }}>
                Lab capacity
              </h3>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--text-xs)', fontFamily: 'var(--font-mono)' }}>
                <span style={{ color: 'var(--text-muted)' }}>OPEN SLOTS:</span>
                <span style={{ color: 'var(--text-strong)', fontWeight: 600 }}>{slots}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--text-xs)', fontFamily: 'var(--font-mono)' }}>
                <span style={{ color: 'var(--text-muted)' }}>COMMITTED:</span>
                <span style={{ color: 'var(--text-strong)', fontWeight: 600 }}>{committed}</span>
              </div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: 'var(--text-xs)',
                  fontFamily: 'var(--font-mono)',
                  borderTop: '1px solid var(--border-subtle)',
                  paddingTop: '8px',
                  marginTop: '2px',
                }}
              >
                <span style={{ color: 'var(--text-muted)' }}>EFFECTIVE VACANT:</span>
                <span style={{ color: 'var(--status-verified-ink)', fontWeight: 600 }}>{effectiveSlots}</span>
              </div>
            </div>

            <hr style={{ border: 'none', borderTop: '1px solid var(--border-subtle)', margin: 0 }} />

            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                <div style={{ color: 'var(--navy-900)' }}>
                  <BookOpen size={18} />
                </div>
                <h3 style={{ margin: 0, fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', fontWeight: 600 }}>
                  Recruiting topics
                </h3>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {areas.map((area, idx) => (
                  <Tag key={idx} tone="accent" style={{ fontSize: '11px', padding: '2px 6px' }}>
                    {area}
                  </Tag>
                ))}
              </div>
            </div>

            {funding && (
              <>
                <hr style={{ border: 'none', borderTop: '1px solid var(--border-subtle)', margin: 0 }} />
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
                    FUNDING AVAILABLE
                  </span>
                  <span style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', color: 'var(--text-strong)', fontWeight: 600 }}>
                    ${funding}/yr
                  </span>
                </div>
              </>
            )}

            <hr style={{ border: 'none', borderTop: '1px solid var(--border-subtle)', margin: 0 }} />

            <Button variant="secondary" size="sm" onClick={handleResetOnboarding} leadingIcon={<Settings size={14} />}>
              Re-run lab setup
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}
