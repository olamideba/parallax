'use client';

export const dynamic = 'force-dynamic';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';
import { api, Outreach, ProfessorProfile } from '@/lib/api';
import { Logo, Wordmark } from '@/components/Logo';
import { Button } from '@/components/Button';
import { Tag } from '@/components/Tag';
import { Loader } from '@/components/Loader';
import { useIsMobile } from '@/lib/useMediaQuery';
import { Inbox, LogOut, Users, BookOpen, Settings, ChevronRight, AlertCircle } from 'lucide-react';

export default function InboxPage() {
  const router = useRouter();
  const isMobile = useIsMobile();
  const [user, setUser] = useState<any>(null);
  const [profile, setProfile] = useState<ProfessorProfile | null>(null);
  const [displayName, setDisplayName] = useState('');
  
  // Local storage fallback states
  const [slots, setSlots] = useState('0');
  const [committed, setCommitted] = useState('0');
  const [areas, setAreas] = useState<string[]>([]);
  const [funding, setFunding] = useState('');

  // Queue states
  const [allOutreaches, setAllOutreaches] = useState<Outreach[]>([]);
  const [activeTab, setActiveTab] = useState<'pending' | 'resolved' | 'declined' | 'replied'>('pending');
  const [loadingQueue, setLoadingQueue] = useState(true);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [apiError, setApiError] = useState<string | null>(null);

  const outreaches = React.useMemo(() => {
    if (activeTab === 'pending') {
      return allOutreaches.filter(
        o => (o.status === 'awaiting_review' && o.decision?.label !== 'decline')
          || o.status === 'pending_triage'
          || o.status === 'held'
      );
    } else if (activeTab === 'resolved') {
      return allOutreaches.filter(o => o.status === 'rejected');
    } else if (activeTab === 'declined') {
      return allOutreaches.filter(o => o.status === 'awaiting_review' && o.decision?.label === 'decline');
    } else if (activeTab === 'replied') {
      return allOutreaches.filter(o => o.status === 'replied');
    }
    return [];
  }, [allOutreaches, activeTab]);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        setUser(session.user);
        setDisplayName(session.user.user_metadata?.display_name || 'Dr. Professor');
        loadBackendProfile();
      } else {
        router.push('/login');
      }
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (session) {
        setUser(session.user);
        setDisplayName(session.user.user_metadata?.display_name || 'Dr. Professor');
        loadBackendProfile();
      } else {
        router.push('/login');
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [router]);

  const loadBackendProfile = async () => {
    try {
      setLoadingProfile(true);
      const prof = await api.getProfessorProfile();
      setProfile(prof);
      setDisplayName(prof.display_name);
      setSlots(String(prof.open_slots));
      setCommitted(String(prof.students_committed));
      setAreas(prof.recruiting_topics);
      if (prof.budget_amount) {
        setFunding(`$${prof.budget_amount.toLocaleString()}/yr (${prof.funding_source || 'Direct'})`);
      } else {
        setFunding('');
      }
    } catch (err) {
      console.warn('Could not load profile from backend:', err);
    } finally {
      setLoadingProfile(false);
    }
  };

  // Fetch outreach queue
  useEffect(() => {
    if (!user) return;

    const fetchQueue = async () => {
      try {
        setLoadingQueue(true);
        setApiError(null);
        const data = await api.getReviewsQueue();
        setAllOutreaches(data);
      } catch (err: any) {
        console.error('Failed to load queue:', err);
        setApiError(err.message || 'Failed to connect to the backend server.');
        setAllOutreaches([]);
      } finally {
        setLoadingQueue(false);
      }
    };

    fetchQueue();
  }, [user]);

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
        <div style={{ maxWidth: '1120px', margin: '0 auto', padding: isMobile ? '14px 16px' : '18px 24px', display: 'flex', alignItems: 'center', gap: '12px' }}>
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
          padding: isMobile ? '28px 16px 64px' : '44px 24px 80px',
          display: 'grid',
          gridTemplateColumns: isMobile ? '1fr' : '1fr 300px',
          gap: isMobile ? '24px' : '32px',
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
              gap: isMobile ? '18px' : '24px',
              paddingBottom: '1px',
              overflowX: 'auto',
              WebkitOverflowScrolling: 'touch',
            }}
          >
            {(['pending', 'resolved', 'declined', 'replied'] as const).map((tab) => {
              const label =
                tab === 'pending' ? 'Pending review' :
                tab === 'resolved' ? 'Auto-resolved' :
                tab === 'declined' ? 'Declined' : 'Replied';
              const isActive = activeTab === tab;
              return (
                <span
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  style={{
                    fontFamily: 'var(--font-sans)',
                    fontSize: 'var(--text-sm)',
                    fontWeight: isActive ? 600 : 500,
                    color: isActive ? 'var(--text-strong)' : 'var(--text-muted)',
                    borderBottom: isActive ? '2px solid var(--navy-900)' : 'none',
                    paddingBottom: '10px',
                    cursor: 'pointer',
                    transition: 'color var(--duration-fast)',
                    whiteSpace: 'nowrap',
                    flexShrink: 0,
                  }}
                >
                  {label}
                </span>
              );
            })}
          </div>

          {/* Connection Error Message */}
          {apiError && (
            <div
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px',
                background: 'rgba(239, 68, 68, 0.08)',
                border: '1px solid rgba(239, 68, 68, 0.2)',
                borderRadius: 'var(--radius-lg)',
                padding: '16px',
                color: 'var(--status-critical-ink)',
                fontFamily: 'var(--font-sans)',
                fontSize: 'var(--text-sm)',
              }}
            >
              <AlertCircle size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
              <div>
                <strong style={{ display: 'block', marginBottom: '4px' }}>Backend connection issue</strong>
                <p style={{ margin: 0, opacity: 0.9, lineHeight: '1.4' }}>
                  {apiError}. Make sure the FastAPI server is running locally on port 8000.
                </p>
              </div>
            </div>
          )}

          {/* Queue List / Empty State / Loading */}
          {loadingQueue ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '60px 0' }}>
              <Loader width={140} label="Loading review queue..." />
            </div>
          ) : outreaches.length === 0 ? (
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
                No items in this queue.
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
                {activeTab === 'pending'
                  ? 'All prospective student outreach items have been processed or resolved.'
                  : activeTab === 'resolved'
                  ? 'No candidates have been auto-rejected/archived by the debate agents.'
                  : activeTab === 'declined'
                  ? 'No candidate applications have been declined.'
                  : 'No candidate applications have been replied to yet.'}
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {outreaches.map((item) => {
                const decisionLabel = item.decision?.label;
                const statusColor =
                  decisionLabel === 'invite'
                    ? 'var(--status-verified-ink)'
                    : decisionLabel === 'request_more_info'
                    ? 'var(--status-triage-ink)'
                    : 'var(--status-critical-ink)';
                
                const statusBg =
                  decisionLabel === 'invite'
                    ? 'rgba(16, 185, 129, 0.08)'
                    : decisionLabel === 'request_more_info'
                    ? 'rgba(245, 158, 11, 0.08)'
                    : 'rgba(239, 68, 68, 0.08)';

                return (
                  <Link
                    href={`/inbox/${item.id}`}
                    key={item.id}
                    style={{ textDecoration: 'none' }}
                  >
                    <div
                      style={{
                        background: 'var(--surface-card)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--radius-xl)',
                        padding: isMobile ? '16px' : '20px 24px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: isMobile ? '12px' : '24px',
                        transition: 'transform var(--duration-fast), box-shadow var(--duration-fast)',
                        cursor: 'pointer',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = 'translateY(-1px)';
                        e.currentTarget.style.boxShadow = 'var(--shadow-md)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'none';
                        e.currentTarget.style.boxShadow = 'none';
                      }}
                    >
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                          <span
                            style={{
                              fontFamily: 'var(--font-sans)',
                              fontSize: 'var(--text-md)',
                              fontWeight: 600,
                              color: 'var(--text-strong)',
                            }}
                          >
                            {item.extracted_profile?.name || item.sender_name || 'Anonymous Applicant'}
                          </span>
                          <span
                            style={{
                              fontFamily: 'var(--font-mono)',
                              fontSize: 'var(--text-xs)',
                              color: 'var(--text-muted)',
                              wordBreak: 'break-all',
                            }}
                          >
                            {item.sender_email}
                          </span>
                        </div>
                        
                        <span
                          style={{
                            fontFamily: 'var(--font-sans)',
                            fontSize: 'var(--text-sm)',
                            fontWeight: 500,
                            color: 'var(--text-body)',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                          }}
                        >
                          {item.subject || '(no subject)'}
                        </span>

                        <p
                          style={{
                            margin: 0,
                            fontFamily: 'var(--font-sans)',
                            fontSize: 'var(--text-sm)',
                            color: 'var(--text-muted)',
                            lineHeight: '1.4',
                            display: '-webkit-box',
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: 'vertical',
                            overflow: 'hidden',
                          }}
                        >
                          {item.body}
                        </p>

                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
                          {item.extracted_profile?.interests.map((interest, idx) => (
                            <span
                              key={idx}
                              style={{
                                fontFamily: 'var(--font-sans)',
                                fontSize: '10px',
                                background: 'var(--gray-50)',
                                border: '1px solid var(--border-subtle)',
                                color: 'var(--text-body)',
                                padding: '1px 6px',
                                borderRadius: 'var(--radius-sm)',
                              }}
                            >
                              {interest}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexShrink: 0 }}>
                        {item.status === 'pending_triage' ? (
                          <span
                            style={{
                              fontFamily: 'var(--font-mono)',
                              fontSize: '10px',
                              fontWeight: 600,
                              letterSpacing: '0.02em',
                              textTransform: 'uppercase',
                              padding: '4px 8px',
                              borderRadius: 'var(--radius-sm)',
                              background: 'rgba(59, 130, 246, 0.08)',
                              color: '#3B82F6',
                              border: '1px solid rgba(59, 130, 246, 0.2)',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '6px',
                            }}
                          >
                            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#3B82F6', display: 'inline-block', animation: 'pulse 1.5s infinite' }} />
                            Processing
                          </span>
                        ) : item.status === 'held' ? (
                          <span
                            title="Debate deferred — your lab is at capacity. Free a slot and re-triage to evaluate."
                            style={{
                              fontFamily: 'var(--font-mono)',
                              fontSize: '10px',
                              fontWeight: 600,
                              letterSpacing: '0.02em',
                              textTransform: 'uppercase',
                              padding: '4px 8px',
                              borderRadius: 'var(--radius-sm)',
                              background: 'rgba(245, 158, 11, 0.08)',
                              color: 'var(--status-triage-ink)',
                              border: '1px solid rgba(245, 158, 11, 0.2)',
                            }}
                          >
                            Held · at capacity
                          </span>
                        ) : item.status === 'replied' ? (
                          <span
                            style={{
                              fontFamily: 'var(--font-mono)',
                              fontSize: '10px',
                              fontWeight: 600,
                              letterSpacing: '0.02em',
                              textTransform: 'uppercase',
                              padding: '4px 8px',
                              borderRadius: 'var(--radius-sm)',
                              background: 'rgba(16, 185, 129, 0.08)',
                              color: 'var(--status-verified-ink)',
                              border: '1px solid rgba(16, 185, 129, 0.2)',
                            }}
                          >
                            Replied
                          </span>
                        ) : item.decision ? (
                          <span
                            style={{
                              fontFamily: 'var(--font-mono)',
                              fontSize: '10px',
                              fontWeight: 600,
                              letterSpacing: '0.02em',
                              textTransform: 'uppercase',
                              padding: '4px 8px',
                              borderRadius: 'var(--radius-sm)',
                              background: statusBg,
                              color: statusColor,
                              border: `1px solid ${statusColor.replace(')', ', 0.12)')}`,
                            }}
                          >
                            {item.decision.label.replace(/_/g, ' ')}
                          </span>
                        ) : null}
                        <ChevronRight size={18} style={{ color: 'var(--text-muted)' }} />
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
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

              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                  borderTop: '1px solid var(--border-subtle)',
                  paddingTop: '8px',
                  marginTop: '2px',
                }}
              >
                <span style={{ color: 'var(--text-muted)', fontSize: 'var(--text-xs)', fontFamily: 'var(--font-mono)' }}>INTAKE ADDRESS:</span>
                {profile?.intake_email ? (
                  <span style={{ color: 'var(--text-strong)', fontSize: '11px', fontFamily: 'var(--font-mono)', wordBreak: 'break-all' }}>
                    {profile.intake_email}
                  </span>
                ) : (
                  <Loader width={72} label="Generating address..." style={{ alignItems: 'flex-start', gap: '6px' }} />
                )}
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
                    BUDGET CONTEXT
                  </span>
                  <span style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', color: 'var(--text-strong)', fontWeight: 600 }}>
                    {funding}
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
