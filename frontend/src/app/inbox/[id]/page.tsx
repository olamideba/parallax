'use client';

export const dynamic = 'force-dynamic';

import React, { useEffect, useRef, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';
import { api, Outreach, Decision } from '@/lib/api';
import { Logo, Wordmark } from '@/components/Logo';
import { Button } from '@/components/Button';
import { Tag } from '@/components/Tag';
import { Loader } from '@/components/Loader';
import { useIsMobile } from '@/lib/useMediaQuery';
import { ArrowLeft, Check, X, AlertCircle, FileText, Send, Sparkles, AlertTriangle, RefreshCw, Play, LogOut } from 'lucide-react';

// Poll while the debate hasn't produced a decision yet — the professor is
// looking at this exact page waiting for triage/debate to land, so a manual
// refresh shouldn't be required to see it resolve.
const DEBATE_POLL_MS = 30_000;

// Verdict display treatment — soft-tinted panel, solid accent, Panchang word.
const VERDICT_META: Record<Decision['label'], { word: string; ink: string; bg: string; accent: string }> = {
  invite: { word: 'Invite', ink: 'var(--status-verified-ink)', bg: 'var(--status-verified-bg)', accent: 'var(--status-verified)' },
  request_more_info: { word: 'More info', ink: 'var(--status-pending-ink)', bg: 'var(--status-pending-bg)', accent: 'var(--status-pending)' },
  decline: { word: 'Decline', ink: 'var(--status-refuted-ink)', bg: 'var(--status-refuted-bg)', accent: 'var(--status-refuted)' },
};

// Split the single rationale paragraph into scannable sections by sentence
// content. Buckets that catch nothing are dropped; short rationales fall back
// to one "Summary" section.
function chunkRationale(rationale: string): { heading: string; sentences: string[] }[] {
  const sentences = (rationale.match(/[^.!?]+[.!?]+["')\]]*|\S[^.!?]*$/g) ?? [rationale])
    .map((s) => s.trim())
    .filter(Boolean);

  const hard: string[] = [];
  const auditor: string[] = [];
  const discrepancies: string[] = [];
  for (const s of sentences) {
    if (/discrepan|inconsist|contradict|conflict|mismatch|overstat|inflat|exaggerat|does not match|doesn't match/i.test(s)) {
      discrepancies.push(s);
    } else if (/auditor|verif|unverif|authentic|receipt|citation|fabricat|cite|publication|claim/i.test(s)) {
      auditor.push(s);
    } else {
      hard.push(s);
    }
  }

  const sections = [
    { heading: 'Hard Requirements', sentences: hard },
    { heading: 'Auditor Insights', sentences: auditor },
    { heading: 'Discrepancies', sentences: discrepancies },
  ].filter((sec) => sec.sentences.length > 0);

  // A one-bucket result means the split found no structure — keep it simple.
  return sections.length > 1 ? sections : [{ heading: 'Summary', sentences }];
}

export default function OutreachDetailPage() {
  const router = useRouter();
  const isMobile = useIsMobile();
  const params = useParams();
  const id = params?.id as string;

  const [user, setUser] = useState<any>(null);
  const [outreach, setOutreach] = useState<Outreach | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [attachmentError, setAttachmentError] = useState<string | null>(null);
  const [displayName, setDisplayName] = useState('');

  // Override Form State
  const [showOverride, setShowOverride] = useState(false);
  const [overrideLabel, setOverrideLabel] = useState<'invite' | 'request_more_info' | 'decline'>('invite');
  const [overrideRationale, setOverrideRationale] = useState('');
  const [overrideReply, setOverrideReply] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Reply Composer State
  const [replyBody, setReplyBody] = useState('');
  const [sendingReply, setSendingReply] = useState(false);

  // Maintenance actions (retriage / delete stub rows)
  const [retriaging, setRetriaging] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Supabase re-validates the session (firing SIGNED_IN/TOKEN_REFRESHED) every
  // time the tab regains focus — not just on real sign-in. Track the last
  // seen user id outside React state so these no-op events don't retrigger
  // the outreach fetch and blank out the page (including any in-progress
  // override form / reply draft) on a simple tab switch.
  const userIdRef = useRef<string | null>(null);
  const hasLoadedRef = useRef(false);

  useEffect(() => {
    const applySession = (session: NonNullable<Awaited<ReturnType<typeof supabase.auth.getSession>>['data']['session']>) => {
      const isNewUser = session.user.id !== userIdRef.current;
      if (isNewUser) hasLoadedRef.current = false;
      userIdRef.current = session.user.id;
      setUser((prev: any) => (prev?.id === session.user.id ? prev : session.user));
      setDisplayName(session.user.user_metadata?.display_name || 'Dr. Professor');
    };

    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        applySession(session);
      } else {
        router.push('/login');
      }
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (session) {
        applySession(session);
      } else {
        router.push('/login');
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [router]);

  const loadOutreach = async () => {
    if (!id) return;
    try {
      // Only show the full-page loader on first load — a background
      // refresh (tab refocus) shouldn't blank the page out from under
      // whatever the professor is doing (override form, reply draft, etc).
      if (!hasLoadedRef.current) setLoading(true);
      setError(null);
      const data = await api.getReviewDetail(id);
      setOutreach(data);
      if (data.decision) {
        setOverrideLabel(data.decision.label);
        setOverrideRationale(data.decision.rationale || '');
        setOverrideReply(data.decision.drafted_reply || '');
        // Pre-fill reply composer with the AI draft (only if not already replied)
        if (data.status !== 'replied') {
          setReplyBody(data.decision.drafted_reply || '');
        }
      }
      hasLoadedRef.current = true;
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Failed to load outreach details from the backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user && id) {
      loadOutreach();
    }
    // Keyed on user?.id (stable across no-op session-refresh events) and id —
    // not the user object, whose identity churns on every tab refocus.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id, id]);

  // Poll for the debate result while none has landed yet. Stops once a
  // decision exists or the outreach reaches a terminal state (replied/
  // rejected), so it doesn't keep hitting the backend after there's nothing
  // left to wait for.
  useEffect(() => {
    if (!outreach || outreach.decision) return;
    if (outreach.status === 'replied' || outreach.status === 'rejected') return;

    const t = setInterval(() => {
      loadOutreach();
    }, DEBATE_POLL_MS);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [outreach?.decision, outreach?.status, id]);

  const handleApprove = async () => {
    if (!outreach) return;
    try {
      setSubmitting(true);
      setError(null);
      await api.approveDecision(outreach.id);
      setSuccessMsg('Decision successfully approved.');
      setTimeout(() => {
        router.push('/inbox');
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Failed to approve decision.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleOverride = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!outreach) return;
    try {
      setSubmitting(true);
      setError(null);
      const updated = await api.overrideDecision(outreach.id, {
        label: overrideLabel,
        rationale: overrideRationale,
        drafted_reply: overrideReply || null,
      });
      setOutreach(updated);
      setSuccessMsg('Decision override saved successfully.');
      setShowOverride(false);
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to submit override.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSendReply = async () => {
    if (!outreach || !replyBody.trim()) return;
    try {
      setSendingReply(true);
      setError(null);
      const updated = await api.sendReply(outreach.id, replyBody);
      setOutreach(updated);
      setSuccessMsg('Reply sent successfully via Brevo.');
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err: any) {
      setError(err.message || 'Failed to send reply.');
    } finally {
      setSendingReply(false);
    }
  };

  const handleRetriage = async () => {
    if (!outreach) return;
    try {
      setRetriaging(true);
      setError(null);
      const updated = await api.retriageOutreach(outreach.id);
      setOutreach(updated);
      setSuccessMsg('Re-queued for Gatekeeper triage.');
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err: any) {
      setError(err.message || 'Failed to re-queue for triage.');
    } finally {
      setRetriaging(false);
    }
  };

  const handleDelete = async () => {
    if (!outreach) return;
    if (!window.confirm('Permanently delete this outreach? This cannot be undone.')) return;
    try {
      setDeleting(true);
      setError(null);
      await api.deleteOutreach(outreach.id);
      router.push('/inbox');
    } catch (err: any) {
      setError(err.message || 'Failed to delete outreach.');
      setDeleting(false);
    }
  };

  const openAttachment = async (index: number) => {
    if (!outreach) return;
    setAttachmentError(null);
    try {
      const url = await api.getAttachmentUrl(outreach.id, index);
      window.open(url, '_blank', 'noopener,noreferrer');
    } catch (err: any) {
      // Shown inline in the attachments block — the page-level banner sits far
      // above the fold, so a failure there would be invisible to the reader.
      setAttachmentError(err.message || 'Failed to open attachment.');
    }
  };

  const handleSignout = async () => {
    await supabase.auth.signOut();
    router.push('/login');
  };

  if (loading) {
    return (
      <Loader fullscreen width={160} label="Loading candidate data..." />
    );
  }

  if (error && !outreach) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--surface-sunken)', padding: '24px' }}>
        <div style={{ background: 'var(--surface-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-xl)', padding: '32px', maxWidth: '480px', width: '100%', textAlign: 'center', boxShadow: 'var(--shadow-md)' }}>
          <AlertCircle size={40} style={{ color: 'var(--status-refuted-ink)', marginBottom: '16px' }} />
          <h2 style={{ margin: '0 0 8px', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-lg)', fontWeight: 600, color: 'var(--text-strong)' }}>Failed to load candidate</h2>
          <p style={{ margin: '0 0 24px', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', color: 'var(--text-muted)', lineHeight: '1.5' }}>{error}</p>
          <Button variant="primary" onClick={() => loadOutreach()}>Retry connection</Button>
          <div style={{ marginTop: '12px' }}>
            <Link href="/inbox" style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)', textDecoration: 'none' }}>Back to Inbox</Link>
          </div>
        </div>
      </div>
    );
  }

  if (!outreach) return null;

  const profile = outreach.extracted_profile;
  const claims = outreach.extracted_claims;
  const decision = outreach.decision;

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--surface-sunken)' }}>
      {/* Top Header */}
      <header style={{ borderBottom: '1px solid var(--border-subtle)', background: 'var(--surface-card)' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: isMobile ? '14px 16px' : '18px 24px', display: 'flex', alignItems: 'center', gap: '12px' }}>
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
            <span style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-sm)', color: 'var(--text-strong)', fontWeight: 400, letterSpacing: 'var(--tracking-snug)' }}>
              {displayName}
            </span>
            <button
              onClick={handleSignout}
              title="Sign out"
              style={{
                background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer',
                display: 'flex', alignItems: 'center', padding: '6px', borderRadius: 'var(--radius-sm)',
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

      {/* Main layout */}
      <main style={{ flex: 1, maxWidth: '1200px', width: '100%', margin: '0 auto', padding: isMobile ? '24px 16px 64px' : '32px 24px 80px', boxSizing: 'border-box' }}>
        
        {/* Back Link & Notifications */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
            <Link href="/inbox" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', textDecoration: 'none', color: 'var(--text-muted)', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)' }}>
              <ArrowLeft size={16} />
              Back to Inbox review queue
            </Link>

            <div style={{ display: 'flex', gap: '8px' }}>
              <Button variant="secondary" size="sm" onClick={handleRetriage} disabled={retriaging || deleting}>
                <RefreshCw size={13} style={{ marginRight: 6 }} />
                {retriaging ? 'Re-queuing...' : 'Re-run triage'}
              </Button>
              <Button variant="secondary" size="sm" onClick={handleDelete} disabled={retriaging || deleting}>
                <X size={13} style={{ marginRight: 6 }} />
                {deleting ? 'Deleting...' : 'Delete'}
              </Button>
            </div>
          </div>

          {successMsg && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.2)', borderRadius: 'var(--radius-md)', padding: '12px 16px', color: 'var(--status-verified-ink)', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)' }}>
              <Check size={18} />
              <span>{successMsg}</span>
            </div>
          )}

          {error && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: 'var(--radius-md)', padding: '12px 16px', color: 'var(--status-refuted-ink)', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)' }}>
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}
        </div>

        {/* Content split grid: left = the static "source file" (candidate facts
            + email), right = the decision console (verdict + reasoning). */}
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1.2fr 1fr', gap: isMobile ? '20px' : '32px', alignItems: 'start' }}>

          {/* LEFT PANE: source file — one continuous scroll, no internal card seams */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div style={{ background: 'var(--surface-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-xl)', padding: isMobile ? '20px' : '28px', boxShadow: 'var(--shadow-sm)' }}>
              <div style={{ marginBottom: '14px' }}>
                <h1 style={{ margin: '0 0 4px', fontFamily: 'var(--font-display)', fontSize: 'var(--text-display-sm)', fontWeight: 700, color: 'var(--text-strong)', letterSpacing: '-0.01em' }}>
                  {profile?.name || outreach.sender_name || 'Anonymous Applicant'}
                </h1>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>
                  {profile?.email || outreach.sender_email}
                </span>
              </div>

              {/* Credentials cluster — degrees + country on one unified row */}
              {((profile?.credentials && profile.credentials.length > 0) || profile?.country) && (
                <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
                  {profile?.credentials?.map((cred, idx) => (
                    <span key={idx} style={{ fontFamily: 'var(--font-display)', fontSize: '11px', background: 'var(--periwinkle-50)', border: '1px solid rgba(26, 54, 93, 0.1)', color: 'var(--navy-900)', padding: '2px 8px', borderRadius: 'var(--radius-sm)', fontWeight: 500 }}>
                      {cred}
                    </span>
                  ))}
                  {profile?.country && (
                    <Tag tone="default" style={{ fontSize: '11px', padding: '2px 8px' }}>{profile.country}</Tag>
                  )}
                </div>
              )}

              {/* Bio details list */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {profile?.interests && profile.interests.length > 0 && (
                  <div>
                    <span style={{ display: 'block', fontFamily: 'var(--font-display)', fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '0.06em', marginBottom: '6px' }}>RECRUITING AREAS OF INTEREST</span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                      {profile.interests.map((interest, idx) => (
                        <Tag key={idx} tone="accent" style={{ fontSize: '11px', padding: '2px 6px' }}>
                          {interest}
                        </Tag>
                      ))}
                    </div>
                  </div>
                )}

                {profile?.funding_context && (
                  <div>
                    <span style={{ display: 'block', fontFamily: 'var(--font-display)', fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '0.06em', marginBottom: '2px' }}>FUNDING CONTEXT</span>
                    <p style={{ margin: 0, fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', color: 'var(--text-body)' }}>{profile.funding_context}</p>
                  </div>
                )}
              </div>

              {/* Original outreach email — same scroll, whitespace does the separation */}
              <div style={{ marginTop: '32px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', minWidth: 0 }}>
                  <span style={{ fontFamily: 'var(--font-display)', fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '0.06em' }}>SUBJECT</span>
                  <span style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-sm)', fontWeight: 700, color: 'var(--text-strong)' }}>
                    {outreach.subject || '(no subject)'}
                  </span>
                </div>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-muted)', flexShrink: 0 }}>
                  RECEIVED: {new Date(outreach.received_at).toLocaleString()}
                </span>
              </div>

              {/* Email Content Body — plain reading text, no box or divider */}
              <div
                style={{
                  marginTop: '16px',
                  fontFamily: 'var(--font-sans)',
                  fontSize: 'var(--text-sm)',
                  color: 'var(--text-body)',
                  lineHeight: '1.65',
                  whiteSpace: 'pre-wrap',
                }}
              >
                {outreach.body}
              </div>

              {/* Attachments */}
              {outreach.attachment_keys && outreach.attachment_keys.length > 0 && (
                <div style={{ marginTop: '20px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <span style={{ fontFamily: 'var(--font-display)', fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '0.06em' }}>ATTACHMENTS</span>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {outreach.attachment_keys.map((attachment, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => openAttachment(idx)}
                        style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'var(--gray-50)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '6px 12px', fontSize: 'var(--text-xs)', color: 'var(--text-body)', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}
                      >
                        <FileText size={14} style={{ color: 'var(--text-muted)' }} />
                        <span>{attachment.filename}</span>
                      </button>
                    ))}
                  </div>
                  {attachmentError && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--status-refuted-ink)', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-xs)' }}>
                      <AlertCircle size={13} style={{ flexShrink: 0 }} />
                      <span>{attachmentError}</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* RIGHT PANE: decision console — verdict first, reasoning under it */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

            {/* Decision Consensus & Actions */}
            <div style={{ background: 'var(--surface-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-xl)', padding: isMobile ? '20px' : '28px', boxShadow: 'var(--shadow-sm)', display: 'flex', flexDirection: 'column', gap: '20px' }}>

              {/* Verdict block — the loudest element on the page */}
              {decision ? (
                <div
                  style={{
                    background: VERDICT_META[decision.label].bg,
                    borderLeft: `4px solid ${VERDICT_META[decision.label].accent}`,
                    borderRadius: 'var(--radius-md)',
                    padding: '18px 20px',
                  }}
                >
                  <span style={{ display: 'block', fontFamily: 'var(--font-display)', fontSize: '10px', color: VERDICT_META[decision.label].ink, letterSpacing: '0.06em', marginBottom: '6px', opacity: 0.8 }}>
                    DEBATE RECOMMENDATION
                  </span>
                  <span
                    style={{
                      display: 'block',
                      fontFamily: 'var(--font-brand)',
                      fontWeight: 700,
                      fontSize: decision.label === 'request_more_info' ? 'var(--text-display-sm)' : 'var(--text-display-lg)',
                      lineHeight: 1.05,
                      textTransform: 'uppercase',
                      color: VERDICT_META[decision.label].ink,
                      overflowWrap: 'break-word',
                    }}
                  >
                    {VERDICT_META[decision.label].word}
                  </span>
                  {decision.overridden_by_professor && (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', marginTop: '10px', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-xs)', color: 'var(--status-pending-ink)', fontWeight: 500 }}>
                      <AlertTriangle size={14} /> Overridden by Professor
                    </span>
                  )}
                </div>
              ) : (
                <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '16px' }}>
                  <span style={{ display: 'block', fontFamily: 'var(--font-display)', fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '0.06em', marginBottom: '8px' }}>DEBATE RECOMMENDATION</span>
                  <span style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>Debate not completed.</span>
                </div>
              )}

              {/* Debate replay entry point — supports the verdict, secondary CTA */}
              {outreach.debate_trace_id && (
                <Link
                  href={`/inbox/${outreach.id}/replay`}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                    textDecoration: 'none', padding: '9px 14px',
                    background: 'var(--action)', color: 'var(--action-text)',
                    border: '1px solid var(--border-default)',
                    borderRadius: 'var(--radius-md)', fontFamily: 'var(--font-display)',
                    fontSize: 'var(--text-sm)', fontWeight: 500,
                  }}
                >
                  <Play size={14} /> Watch the debate replay
                </Link>
              )}

              {/* Rationale — chunked into scannable sections */}
              {decision?.rationale && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  <span style={{ display: 'block', fontFamily: 'var(--font-display)', fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '0.06em' }}>DECISION RATIONALE</span>
                  {chunkRationale(decision.rationale).map(({ heading, sentences }) => (
                    <div key={heading}>
                      <span style={{ display: 'block', fontFamily: 'var(--font-display)', fontSize: 'var(--text-sm)', fontWeight: 700, color: 'var(--text-strong)', marginBottom: '4px' }}>
                        {heading}
                      </span>
                      <p style={{ margin: 0, fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', color: 'var(--text-body)', lineHeight: '1.55' }}>
                        {sentences.join(' ')}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              {/* Status-aware: Pending Triage notice */}
              {outreach.status === 'pending_triage' && (
                <div style={{
                  display: 'flex', alignItems: 'center', gap: '10px',
                  background: 'rgba(245, 158, 11, 0.06)', border: '1px solid rgba(245, 158, 11, 0.2)',
                  borderRadius: 'var(--radius-md)', padding: '12px 14px',
                  fontFamily: 'var(--font-sans)', fontSize: 'var(--text-xs)', color: 'var(--status-pending-ink)',
                }}>
                  <RefreshCw size={14} className="animate-spin" />
                  <span>This outreach is being processed by the AI pipeline. Actions will be available once triage is complete.</span>
                </div>
              )}

              {/* Status-aware: Replied banner */}
              {outreach.status === 'replied' && (
                <div style={{
                  display: 'flex', alignItems: 'center', gap: '10px',
                  background: 'rgba(16, 185, 129, 0.06)', border: '1px solid rgba(16, 185, 129, 0.2)',
                  borderRadius: 'var(--radius-md)', padding: '12px 14px',
                  fontFamily: 'var(--font-sans)', fontSize: 'var(--text-xs)', color: 'var(--status-verified-ink)',
                }}>
                  <Check size={14} />
                  <span>
                    Reply sent{outreach.replied_at ? ` on ${new Date(outreach.replied_at).toLocaleString()}` : ''}. No further action needed.
                  </span>
                </div>
              )}

              {/* Reply Composer */}
              {outreach.status !== 'pending_triage' && outreach.status !== 'rejected' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <label style={{ fontFamily: 'var(--font-display)', fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '0.06em' }}>
                    {outreach.status === 'replied' ? 'SENT REPLY' : 'REPLY DRAFT'}
                  </label>
                  <textarea
                    value={outreach.status === 'replied' ? (decision?.drafted_reply || replyBody) : replyBody}
                    onChange={(e) => {
                      if (outreach.status !== 'replied') setReplyBody(e.target.value);
                    }}
                    readOnly={outreach.status === 'replied'}
                    placeholder="Edit the reply draft before sending..."
                    style={{
                      minHeight: '140px',
                      padding: '12px',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border-subtle)',
                      background: outreach.status === 'replied' ? 'var(--surface-sunken)' : 'var(--surface-card)',
                      fontFamily: 'var(--font-sans)',
                      fontSize: 'var(--text-xs)',
                      color: outreach.status === 'replied' ? 'var(--text-muted)' : 'var(--text-strong)',
                      outline: 'none',
                      resize: 'vertical',
                      lineHeight: '1.5',
                      cursor: outreach.status === 'replied' ? 'default' : 'text',
                    }}
                  />
                  {outreach.status !== 'replied' && (
                    <Button
                      variant="primary"
                      style={{ width: '100%', justifyContent: 'center', display: 'flex', alignItems: 'center', gap: '8px' }}
                      onClick={handleSendReply}
                      disabled={sendingReply || !replyBody.trim()}
                    >
                      <Send size={14} />
                      {sendingReply ? 'Sending...' : 'Send Reply via Brevo'}
                    </Button>
                  )}
                </div>
              )}

              {/* Action buttons (Approve / Override Trigger) — hidden when replied or pending */}
              {outreach.status === 'awaiting_review' && !showOverride && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '4px' }}>
                  {decision && (
                    <Button variant="secondary" style={{ width: '100%', justifyContent: 'center' }} onClick={handleApprove} disabled={submitting}>
                      {submitting ? 'Approving...' : 'Approve Decision (no reply)'}
                    </Button>
                  )}
                  <Button variant="secondary" style={{ width: '100%', justifyContent: 'center' }} onClick={() => setShowOverride(true)}>
                    Override Decision
                  </Button>
                </div>
              )}

              {/* Override Collapsible Form */}
              {showOverride && (
                <form onSubmit={handleOverride} style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <h4 style={{ margin: 0, fontFamily: 'var(--font-display)', fontSize: 'var(--text-sm)', fontWeight: 700 }}>Specify decision override</h4>
                  
                  {/* Label selector */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <label style={{ fontFamily: 'var(--font-display)', fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '0.06em' }}>NEW DECISION STATUS</label>
                    <select
                      value={overrideLabel}
                      onChange={(e) => setOverrideLabel(e.target.value as any)}
                      style={{
                        padding: '10px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)',
                        background: 'var(--surface-card)', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)',
                        color: 'var(--text-strong)', outline: 'none',
                      }}
                    >
                      <option value="invite">Invite candidate to interview</option>
                      <option value="request_more_info">Request more details</option>
                      <option value="decline">Decline application</option>
                    </select>
                  </div>

                  {/* Rationale input */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <label style={{ fontFamily: 'var(--font-display)', fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '0.06em' }}>RATIONALE</label>
                    <textarea
                      value={overrideRationale}
                      onChange={(e) => setOverrideRationale(e.target.value)}
                      placeholder="Explain your decision..."
                      required
                      style={{
                        minHeight: '80px', padding: '10px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)',
                        background: 'var(--surface-card)', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)',
                        color: 'var(--text-strong)', outline: 'none', resize: 'vertical',
                      }}
                    />
                  </div>

                  {/* Draft Reply edit */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <label style={{ fontFamily: 'var(--font-display)', fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '0.06em' }}>REPLY DRAFT (OPTIONAL)</label>
                    <textarea
                      value={overrideReply}
                      onChange={(e) => setOverrideReply(e.target.value)}
                      placeholder="Write your email response draft here..."
                      style={{
                        minHeight: '120px', padding: '10px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)',
                        background: 'var(--surface-card)', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-xs)',
                        color: 'var(--text-strong)', outline: 'none', resize: 'vertical',
                      }}
                    />
                  </div>

                  {/* Action buttons */}
                  <div style={{ display: 'flex', gap: '10px', marginTop: '4px' }}>
                    <Button variant="primary" type="submit" style={{ flex: 1, justifyContent: 'center' }} disabled={submitting}>
                      {submitting ? 'Saving...' : 'Submit Override'}
                    </Button>
                    <Button variant="secondary" type="button" onClick={() => setShowOverride(false)}>
                      Cancel
                    </Button>
                  </div>
                </form>
              )}
            </div>

            {/* Debate Claim Extraction Panel */}
            <div style={{ background: 'var(--surface-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-xl)', padding: '24px', boxShadow: 'var(--shadow-sm)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                <Sparkles size={16} style={{ color: 'var(--navy-900)' }} />
                <h3 style={{ margin: 0, fontFamily: 'var(--font-display)', fontSize: 'var(--text-sm)', fontWeight: 700 }}>Extracted Fact Verification</h3>
              </div>

              {claims && claims.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {claims.map((claim, idx) => {
                    const statusIcon = claim.verified === true ? <Check size={12} /> : claim.verified === false ? <X size={12} /> : <span style={{ fontWeight: 600 }}>—</span>;
                    const statusColor = claim.verified === true ? 'var(--status-verified-ink)' : claim.verified === false ? 'var(--status-refuted-ink)' : 'var(--text-muted)';
                    const statusBg = claim.verified === true ? 'rgba(16, 185, 129, 0.08)' : claim.verified === false ? 'rgba(239, 68, 68, 0.08)' : 'rgba(0, 0, 0, 0.04)';

                    return (
                      <div key={idx} style={{ background: 'var(--surface-sunken)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <div style={{ display: 'flex', alignItems: 'start', justifyContent: 'space-between', gap: '12px' }}>
                          <p style={{ margin: 0, fontFamily: 'var(--font-sans)', fontSize: 'var(--text-xs)', color: 'var(--text-body)', lineHeight: '1.4' }}>
                            &ldquo;{claim.text}&rdquo;
                          </p>
                          <div style={{ width: '18px', height: '18px', borderRadius: '50%', background: statusBg, color: statusColor, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, border: `1px solid ${statusColor.replace(')', ', 0.15)')}` }}>
                            {statusIcon}
                          </div>
                        </div>
                        {claim.receipt && (
                          <div style={{ borderTop: '1px dashed var(--border-subtle)', paddingTop: '6px', fontSize: '11px', fontFamily: 'var(--font-sans)', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                            <strong>Verification note:</strong> {claim.receipt}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '24px 0', border: '1px dashed var(--border-subtle)', borderRadius: 'var(--radius-lg)' }}>
                  <span style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>No verification claims found.</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
