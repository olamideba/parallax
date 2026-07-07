'use client';

export const dynamic = 'force-dynamic';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { api, PublicationInput, PublicationStatus } from '@/lib/api';
import { Logo, Wordmark } from '@/components/Logo';
import { Button } from '@/components/Button';
import { Input } from '@/components/Input';
import { Checkbox } from '@/components/Checkbox';
import { Tag } from '@/components/Tag';
import { useIsMobile } from '@/lib/useMediaQuery';
import {
  Check,
  CheckCircle,
  AlertTriangle,
  Loader,
  ArrowLeft,
  ArrowRight,
  Upload,
  X,
  Plus,
  Lock,
  XCircle,
  Share2,
  Workflow,
  Copy,
} from 'lucide-react';

interface Paper {
  id: number;
  backendId: string | null;    // set after PUT returns
  storageKey: string | null;   // set after PDF upload
  t: string;
  v: string;
  cites: number;
  state: 'resolving' | 'indexed' | 'paywalled' | 'failed';
  doi: string;
}

const statusToState = (s: PublicationStatus): Paper['state'] => ({
  pending:      'resolving',
  indexing:     'resolving',
  indexed:      'indexed',
  needs_upload: 'paywalled',
  failed:       'failed',
} as Record<PublicationStatus, Paper['state']>)[s] ?? 'failed';

interface StepperProps {
  step: number;
  steps: string[];
}

function Stepper({ step, steps }: StepperProps) {
  const isMobile = useIsMobile();
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 0, marginBottom: isMobile ? '28px' : '36px' }}>
      {steps.flatMap((s, i) => {
        const state = i < step ? 'done' : i === step ? 'current' : 'todo';
        // On mobile, only the active step keeps its text label so the rail fits.
        const showLabel = !isMobile || state === 'current';
        const node = (
          <div key={'s' + i} style={{ display: 'flex', alignItems: 'center', gap: showLabel ? '10px' : 0 }}>
            <span
              style={{
                width: 26, height: 26, borderRadius: '999px', flexShrink: 0,
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                fontFamily: 'var(--font-mono)', fontSize: '12px', fontWeight: 600,
                background: state === 'done' ? 'var(--status-verified)' : state === 'current' ? 'var(--navy-900)' : 'var(--surface-muted)',
                color: state === 'todo' ? 'var(--text-subtle)' : 'var(--white)',
                border: state === 'current' ? '2px solid var(--periwinkle-400)' : 'none',
              }}
            >
              {state === 'done' ? <Check size={14} color="var(--white)" /> : String(i + 1)}
            </span>
            {showLabel && (
              <span
                style={{
                  fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)',
                  fontWeight: state === 'current' ? 600 : 500,
                  color: state === 'todo' ? 'var(--text-subtle)' : 'var(--text-strong)',
                  whiteSpace: 'nowrap'
                }}
              >
                {s}
              </span>
            )}
          </div>
        );
        const conn = i < steps.length - 1 ? (
          <div key={'c' + i} style={{ flex: 1, height: 1, background: 'var(--border-default)', margin: isMobile ? '0 8px' : '0 14px', minWidth: isMobile ? 12 : 24 }} />
        ) : null;
        return conn ? [node, conn] : [node];
      })}
    </div>
  );
}

function ResolutionPill({ state }: { state: Paper['state'] }) {
  const configs = {
    resolving: { label: 'Resolving…', color: 'var(--status-pending-ink)', bg: 'var(--status-pending-bg)', icon: <Loader size={13} style={{ animation: 'spin 1s linear infinite' }} /> },
    indexed:   { label: 'Indexed',    color: 'var(--status-verified-ink)', bg: 'var(--status-verified-bg)', icon: <CheckCircle size={13} /> },
    paywalled: { label: 'Needs PDF',  color: 'var(--agent-3-ink)', bg: 'var(--agent-3-bg)', icon: <Lock size={13} /> },
    failed:    { label: 'Not found',  color: 'var(--status-refuted-ink)',  bg: 'var(--status-refuted-bg)',  icon: <XCircle size={13} /> },
  };
  const cfg = configs[state] || { label: state, color: 'var(--text-muted)', bg: 'var(--surface-muted)', icon: null };
  return (
    <div
      style={{
        display: 'inline-flex', alignItems: 'center', gap: '5px',
        padding: '3px 9px', borderRadius: '999px',
        background: cfg.bg, color: cfg.color,
        fontFamily: 'var(--font-sans)', fontSize: '12px', fontWeight: 500,
        whiteSpace: 'nowrap',
      }}
    >
      {cfg.icon}
      {cfg.label}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default function OnboardingPage() {
  const router = useRouter();
  const isMobile = useIsMobile();

  const STEPS = ['Publications', 'Lab capacity', 'Intake address', 'Review'];
  const [step, setStep] = useState(0);

  /* — Publications state — */
  const [doiText, setDoiText] = useState('');
  const [papers, setPapers] = useState<Paper[]>([]);
  const [dropError, setDropError] = useState<string | null>(null);
  const [retryErrors, setRetryErrors] = useState<Record<number, string>>({});

  /* — Lab capacity state — */
  const [slots, setSlots] = useState(3);
  const [committed, setCommitted] = useState(1);
  const [fundingAmount, setFundingAmount] = useState('');
  const [fundingSource, setFundingSource] = useState('');
  const [areas, setAreas] = useState(['Sparse attention', 'Long-context retrieval', 'Efficient transformers']);
  const [archiveDeclines, setArchiveDeclines] = useState(true);
  const [holdAtCapacity, setHoldAtCapacity] = useState(true);
  const [customInstructions, setCustomInstructions] = useState('');
  const [institution, setInstitution] = useState('');
  const [institutionCountry, setInstitutionCountry] = useState('');
  const [saving, setSaving] = useState(false);

  /* — Intake email state — */
  const [intakeEmail, setIntakeEmail] = useState('');
  const [testingIntake, setTestingIntake] = useState(false);
  const [testIntakeSuccess, setTestIntakeSuccess] = useState(false);
  const [testIntakeError, setTestIntakeError] = useState<string | null>(null);
  const [intakeCopied, setIntakeCopied] = useState(false);
  // Two equally valid ways to get mail flowing — sharing the address directly
  // is the simplest path; forwarding is for professors who'd rather keep
  // using their existing inbox. Neither is "the setup", just a preference.
  const [intakeMode, setIntakeMode] = useState<'share' | 'forward'>('share');

  const handleTestIntake = async () => {
    setTestingIntake(true);
    setTestIntakeSuccess(false);
    setTestIntakeError(null);
    try {
      await api.testIntake();
      setTestIntakeSuccess(true);
    } catch (err: any) {
      setTestIntakeError(err.message || 'Failed to inject test email.');
    } finally {
      setTestingIntake(false);
    }
  };

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        loadData();
      } else {
        router.push('/login');
      }
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (session) {
        loadData();
      } else {
        router.push('/login');
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [router]);

  const loadData = async () => {
    try {
      const prof = await api.getProfessorProfile();
      if (prof) {
        setSlots(prof.open_slots);
        setCommitted(prof.students_committed);
        setFundingAmount(prof.budget_amount ? String(prof.budget_amount) : '');
        setFundingSource(prof.funding_source || '');
        setIntakeEmail(prof.intake_email || '');
        if (prof.recruiting_topics && prof.recruiting_topics.length > 0) {
          setAreas(prof.recruiting_topics);
        }
        setArchiveDeclines(prof.auto_resolve_declines ?? true);
        setHoldAtCapacity(prof.hold_when_at_capacity ?? true);
        setCustomInstructions(prof.custom_instructions || '');
        setInstitution(prof.institution || '');
        setInstitutionCountry(prof.institution_country || '');
      }
      
      const pubs = await api.getPublications();
      if (pubs && pubs.length > 0) {
        setPapers(pubs.map((p, idx) => ({
          id: idx + 1,
          backendId: p.id,
          storageKey: p.storage_key,
          t: p.title ?? '—',
          v: '—',
          cites: 0,
          state: statusToState(p.status),
          doi: p.doi ?? p.url ?? '',
        })));
      }
    } catch (err) {
      console.warn('Failed to load onboarding info from backend:', err);
    }
  };

  const handleResolve = async () => {
    if (!doiText.trim()) return;
    const lines = doiText.trim().split(/\n+/).map(l => l.trim()).filter(Boolean);
    setDoiText('');

    const tempIds = lines.map((_, i) => Date.now() + i);
    const optimistic: Paper[] = lines.map((line, i) => ({
      id: tempIds[i],
      backendId: null,
      storageKey: null,
      t: line.slice(0, 60) + (line.length > 60 ? '…' : ''),
      v: '—', cites: 0, state: 'resolving' as const, doi: line,
    }));
    setPapers(p => [...p, ...optimistic]);

    const payloads = lines.map(line => {
      const isUrl = line.startsWith('http://') || line.startsWith('https://');
      return {
        title: null,
        doi: isUrl ? null : line,
        url: isUrl ? line : null,
        storage_key: null,
      };
    });

    try {
      const created = await api.addPublications(payloads);
      setPapers(prev => prev.map(p => {
        const idx = tempIds.indexOf(p.id);
        if (idx === -1) return p;
        const pub = created[idx];
        return { ...p, backendId: pub.id, storageKey: pub.storage_key, t: pub.title ?? p.t, state: statusToState(pub.status) };
      }));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to add publications';
      setPapers(prev => prev.map(p =>
        tempIds.includes(p.id) ? { ...p, state: 'failed' as const } : p
      ));
      setDropError(msg);
    }
  };

  const handlePdfFiles = async (files: File[]) => {
    setDropError(null);
    for (const file of files) {
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        setDropError('Only PDF files are supported');
        continue;
      }
      if (file.size > 25 * 1024 * 1024) {
        setDropError('File exceeds 25 MB limit');
        continue;
      }
      const newId = Date.now() + Math.random();
      const placeholder: Paper = {
        id: newId,
        backendId: null,
        storageKey: null,
        t: file.name.replace(/\.pdf$/i, ''),
        v: '—', cites: 0, state: 'resolving', doi: '',
      };
      setPapers(p => [...p, placeholder]);
      try {
        const { storage_key } = await api.uploadPublicationPdf(file);
        setPapers(p => p.map(pp =>
          pp.id === newId ? { ...pp, storageKey: storage_key } : pp
        ));
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Upload failed';
        if (msg.includes('25 MB') || msg.includes('413')) {
          setDropError('File exceeds 25 MB limit');
        } else if (msg.includes('415') || msg.includes('PDF')) {
          setDropError('Only PDF files are supported');
        } else {
          setDropError(msg);
        }
        setPapers(p => p.filter(pp => pp.id !== newId));
      }
    }
  };

  const handleRetryUpload = async (paper: Paper, file: File) => {
    if (!paper.backendId) return;
    setRetryErrors(e => ({ ...e, [paper.id]: '' }));
    setPapers(ps => ps.map(p => p.id === paper.id ? { ...p, state: 'resolving' } : p));
    try {
      await api.uploadPublicationPdf(file, paper.backendId);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed';
      setPapers(ps => ps.map(p => p.id === paper.id ? { ...p, state: 'needs_upload' as Paper['state'] } : p));
      setRetryErrors(e => ({ ...e, [paper.id]: msg }));
    }
  };

  // failed: no file picker — PDF already in R2, just re-trigger ingestion
  const handleReingest = async (paper: Paper) => {
    if (!paper.backendId) return;
    setRetryErrors(e => ({ ...e, [paper.id]: '' }));
    setPapers(ps => ps.map(p => p.id === paper.id ? { ...p, state: 'resolving' } : p));
    try {
      await api.reingestPublication(paper.backendId);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Retry failed';
      setPapers(ps => ps.map(p => p.id === paper.id ? { ...p, state: 'failed' } : p));
      setRetryErrors(e => ({ ...e, [paper.id]: msg }));
    }
  };

  const handleFinishSetup = async () => {
    setSaving(true);
    try {
      // Publications are already saved individually as the user adds them.
      // Just persist the profile. Completion itself is derived from this
      // data on next login/root visit (open_slots/recruiting_topics set) —
      // there's no separate "completed" flag to write.
      const budgetAmountInt = parseInt(fundingAmount.replace(/,/g, '')) || null;
      await api.patchProfessorProfile({
        open_slots: slots,
        students_committed: committed,
        budget_amount: budgetAmountInt,
        funding_source: fundingSource || null,
        recruiting_topics: areas,
        auto_resolve_declines: archiveDeclines,
        hold_when_at_capacity: holdAtCapacity,
        custom_instructions: customInstructions.trim() || null,
        institution: institution.trim() || null,
        institution_country: institutionCountry.trim() || null,
      });

      router.push('/inbox');
    } catch (err) {
      console.error(err);
      setSaving(false);
    }
  };

  useEffect(() => {
    const hasLive = papers.some(p => p.state === 'resolving');
    if (!hasLive) return;
    const t = setInterval(async () => {
      try {
        const pubs = await api.getPublications();
        setPapers(prev => prev.map(p => {
          if (!p.backendId) return p;
          const fresh = pubs.find(q => q.id === p.backendId);
          if (!fresh) return p;
          return {
            ...p,
            t: fresh.title ?? p.t,
            state: statusToState(fresh.status),
            storageKey: fresh.storage_key ?? p.storageKey,
          };
        }));
      } catch {
      }
    }, 9000);
    return () => clearInterval(t);
  }, [papers]);

  const cardWrap = (children: React.ReactNode) => (
    <div
      style={{
        background: 'var(--surface-card)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-xl)',
        boxShadow: 'var(--shadow-md)',
        padding: isMobile ? '24px 20px' : '36px 40px'
      }}
    >
      {children}
    </div>
  );

  const monoHeader = (t: string) => (
    <div
      style={{
        fontFamily: 'var(--font-mono)',
        fontSize: '10px',
        letterSpacing: 'var(--tracking-caps)',
        textTransform: 'uppercase',
        color: 'var(--text-muted)',
        marginBottom: '8px'
      }}
    >
      {t}
    </div>
  );

  const h2Title = (t: string) => (
    <h2
      style={{
        margin: '0 0 6px',
        fontFamily: 'var(--font-display)',
        fontSize: 'var(--text-display-md)',
        fontWeight: 600,
        color: 'var(--text-strong)',
        letterSpacing: '-0.015em',
        lineHeight: 1.15
      }}
    >
      {t}
    </h2>
  );

  const subDescription = (t: string) => (
    <p
      style={{
        margin: '0 0 28px',
        fontFamily: 'var(--font-sans)',
        fontSize: 'var(--text-md)',
        color: 'var(--text-muted)',
        lineHeight: 'var(--leading-relaxed)',
        maxWidth: '60ch'
      }}
    >
      {t}
    </p>
  );

  const sectionRule = (
    <hr style={{ border: 'none', borderTop: '1px solid var(--border-subtle)', margin: '28px 0' }} />
  );

  const indexed = papers.filter(p => p.state === 'indexed').length;
  const needs = papers.filter(p => p.state === 'paywalled' || p.state === 'failed');

  let body;
  if (step === 0) {
    body = cardWrap(
      <>
        {monoHeader('Step 1 of 3')}
        {h2Title('Connect your published work')}
        {subDescription('Parallax grounds every debate in your own research. Upload your paper PDFs to add them directly — the fastest, most reliable way to index your work. You can also paste DOIs or arXiv URLs below, and the system fetches full text where open-access and prompts you to upload PDFs for anything paywalled.')}

        <div
          style={{ border: '2px dashed var(--border-default)', borderRadius: 'var(--radius-xl)', padding: '36px 24px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '10px', textAlign: 'center', background: 'var(--surface-sunken)', color: 'var(--text-muted)', marginBottom: dropError ? '8px' : '24px', cursor: 'pointer', position: 'relative' }}
          onDragOver={e => { e.preventDefault(); e.stopPropagation(); }}
          onDrop={e => {
            e.preventDefault();
            e.stopPropagation();
            const files = Array.from(e.dataTransfer.files);
            handlePdfFiles(files);
          }}
          onClick={() => {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.pdf';
            input.multiple = true;
            input.onchange = () => {
              if (input.files) handlePdfFiles(Array.from(input.files));
            };
            input.click();
          }}
        >
          <div
            style={{
              width: 44, height: 44, borderRadius: '999px', flexShrink: 0,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: 'var(--surface-card)', border: '1px solid var(--border-subtle)',
            }}
          >
            <Upload size={20} style={{ color: 'var(--navy-900)' }} />
          </div>
          <span style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-md)', fontWeight: 600, color: 'var(--text-strong)' }}>
            Drop PDFs here to add papers directly
          </span>
          <span style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', color: 'var(--text-subtle)' }}>
            The fastest way to index your work — drag and drop one or more paper PDFs.
          </span>
        </div>
        {dropError && (
          <div style={{ marginBottom: '16px', fontFamily: 'var(--font-sans)', fontSize: '12px', color: 'var(--status-refuted-ink)', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <XCircle size={13} />{dropError}
          </div>
        )}

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
          <div style={{ flex: 1, height: 1, background: 'var(--border-subtle)' }} />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-subtle)', letterSpacing: 'var(--tracking-caps)', textTransform: 'uppercase' }}>
            or add by DOI / URL
          </span>
          <div style={{ flex: 1, height: 1, background: 'var(--border-subtle)' }} />
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', fontWeight: 500, color: 'var(--text-strong)', marginBottom: '6px' }}>
            DOIs or arXiv URLs
          </label>
          <textarea
            value={doiText}
            onChange={e => setDoiText(e.target.value)}
            placeholder="10.1145/3534678&#10;https://arxiv.org/abs/2205.01068&#10;10.18653/v1/2023.acl-long.42&#10;…"
            style={{
              width: '100%', minHeight: 96, resize: 'vertical', boxSizing: 'border-box',
              fontFamily: 'var(--font-mono)', fontSize: '12px', lineHeight: 1.6,
              border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)',
              padding: '10px 12px', background: 'var(--surface-card)', color: 'var(--text-body)',
              outline: 'none',
            }}
          />
          <div style={{ marginTop: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
            <span style={{ fontFamily: 'var(--font-sans)', fontSize: '12px', color: 'var(--text-subtle)' }}>
              One DOI or arXiv URL per line. Paywalled papers will prompt for PDF upload.
            </span>
            <Button variant="secondary" onClick={handleResolve} disabled={!doiText.trim()} style={{ flexShrink: 0 }}>
              Resolve & index
            </Button>
          </div>
        </div>

        {papers.length > 0 && (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
              <CheckCircle size={15} style={{ color: 'var(--status-verified)' }} />
              <span style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--status-verified-ink)' }}>
                {indexed} of {papers.length} papers indexed
              </span>
              {needs.length > 0 && (
                <span style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', color: 'var(--agent-3-ink)' }}>
                  · {needs.length} need attention
                </span>
              )}
            </div>
            <div style={{ border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
              {papers.map((p, i) => (
                <div
                  key={p.id}
                  style={{
                    display: 'flex', alignItems: 'center', gap: '14px', padding: '11px 16px',
                    borderTop: i ? '1px solid var(--border-subtle)' : 'none',
                    background: p.state === 'paywalled' ? 'var(--agent-3-bg)' : p.state === 'failed' ? 'var(--status-refuted-bg)' : 'transparent'
                  }}
                >
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-strong)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {p.t}
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                      {p.v !== '—' ? `${p.v} · ${p.cites} citations` : p.doi}
                    </div>
                  </div>
                  <ResolutionPill state={p.state} />
                  {p.state === 'paywalled' && p.backendId && (
                    <>
                      <Button
                        variant="ghost"
                        style={{ padding: '4px 10px', fontSize: '12px' }}
                        onClick={() => {
                          const input = document.createElement('input');
                          input.type = 'file';
                          input.accept = '.pdf';
                          input.onchange = (e) => {
                            const file = (e.target as HTMLInputElement).files?.[0];
                            if (file) handleRetryUpload(p, file);
                          };
                          input.click();
                        }}
                      >
                        Upload PDF
                      </Button>
                      {retryErrors[p.id] && (
                        <span style={{ fontSize: '11px', color: 'var(--status-refuted-ink)' }}>
                          {retryErrors[p.id]}
                        </span>
                      )}
                    </>
                  )}
                  {p.state === 'failed' && p.backendId && (
                    <>
                      <Button
                        variant="ghost"
                        style={{ padding: '4px 10px', fontSize: '12px' }}
                        onClick={() => handleReingest(p)}
                      >
                        Retry
                      </Button>
                      {retryErrors[p.id] && (
                        <span style={{ fontSize: '11px', color: 'var(--status-refuted-ink)' }}>
                          {retryErrors[p.id]}
                        </span>
                      )}
                    </>
                  )}
                  <button
                    onClick={() => setPapers(pp => pp.filter(x => x.id !== p.id))}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-subtle)', padding: '4px', display: 'flex', alignItems: 'center' }}
                  >
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </>
    );
  } else if (step === 1) {
    body = cardWrap(
      <>
        {monoHeader('Step 2 of 3')}
        {h2Title('Declare your lab capacity')}
        {subDescription('Agents weigh every candidate against these constraints. Capacity is a hard signal, not a guess — set it accurately and update it as slots fill.')}

        <div style={{ marginBottom: '28px' }}>
          {monoHeader('Open student slots this cycle')}
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {[0, 1, 2, 3, 4, 5].map(n => (
              <button
                key={n}
                onClick={() => setSlots(n)}
                style={{
                  width: 48, height: 48, borderRadius: 'var(--radius-md)', cursor: 'pointer',
                  fontFamily: 'var(--font-mono)', fontSize: 'var(--text-lg)', fontWeight: 600,
                  border: '1px solid ' + (slots === n ? 'var(--navy-900)' : 'var(--border-default)'),
                  background: slots === n ? 'var(--navy-900)' : 'var(--surface-card)',
                  color: slots === n ? 'var(--white)' : 'var(--text-body)',
                }}
              >
                {n}
              </button>
            ))}
          </div>
        </div>

        <div style={{ marginBottom: '28px' }}>
          {monoHeader('Students already committed')}
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {[0, 1, 2, 3, 4].map(n => (
              <button
                key={n}
                onClick={() => setCommitted(n)}
                style={{
                  width: 48, height: 48, borderRadius: 'var(--radius-md)', cursor: 'pointer',
                  fontFamily: 'var(--font-mono)', fontSize: 'var(--text-lg)', fontWeight: 600,
                  border: '1px solid ' + (committed === n ? 'var(--periwinkle-700)' : 'var(--border-default)'),
                  background: committed === n ? 'var(--periwinkle-100)' : 'var(--surface-card)',
                  color: committed === n ? 'var(--periwinkle-700)' : 'var(--text-body)',
                }}
              >
                {n}
              </button>
            ))}
          </div>
          <p style={{ fontFamily: 'var(--font-sans)', fontSize: '12px', color: 'var(--text-subtle)', margin: '8px 0 0' }}>
            {committed > 0
              ? `${committed} student${committed > 1 ? 's' : ''} already committed · ${Math.max(0, slots - committed)} effective open slot${Math.max(0, slots - committed) !== 1 ? 's' : ''}`
              : 'No students committed yet'}
          </p>
        </div>

        {sectionRule}

        <div style={{ marginBottom: '28px' }}>
          {monoHeader('Funding capacity')}
          <p style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', color: 'var(--text-muted)', margin: '0 0 14px', maxWidth: '56ch' }}>
            Declared by you, never inferred about the applicant. Used to assess feasibility — not shown to candidates.
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: '14px' }}>
            <div>
              <label style={{ display: 'block', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', fontWeight: 500, color: 'var(--text-strong)', marginBottom: '6px' }}>
                Available budget
              </label>
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <span style={{ position: 'absolute', left: 12, fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)', color: 'var(--text-muted)', pointerEvents: 'none' }}>
                  $
                </span>
                <input
                  type="text"
                  value={fundingAmount}
                  onChange={e => setFundingAmount(e.target.value)}
                  placeholder="40,000"
                  style={{
                    width: '100%', boxSizing: 'border-box',
                    paddingLeft: '26px', paddingRight: '12px', height: '40px',
                    fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)',
                    border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)',
                    background: 'var(--surface-card)', color: 'var(--text-body)', outline: 'none',
                  }}
                />
              </div>
              <p style={{ fontFamily: 'var(--font-sans)', fontSize: '11px', color: 'var(--text-subtle)', margin: '5px 0 0' }}>
                Per student per year, USD
              </p>
            </div>
            <div>
              <label style={{ display: 'block', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', fontWeight: 500, color: 'var(--text-strong)', marginBottom: '6px' }}>
                Funding source
              </label>
              <select
                value={fundingSource}
                onChange={e => setFundingSource(e.target.value)}
                style={{
                  width: '100%', height: '40px', boxSizing: 'border-box',
                  padding: '0 12px', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)',
                  border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)',
                  background: 'var(--surface-card)', color: fundingSource ? 'var(--text-body)' : 'var(--text-subtle)', outline: 'none',
                  appearance: 'none',
                }}
              >
                <option value="" disabled>Select source</option>
                <option value="department">Department funding</option>
                <option value="professor">Professor / grant funding</option>
                <option value="university">University / fellowship</option>
                <option value="mixed">Mixed sources</option>
              </select>
            </div>
          </div>
        </div>

        {sectionRule}

        <div style={{ marginBottom: '28px' }}>
          {monoHeader('Projects and topics currently recruiting for')}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '12px' }}>
            {areas.map((a, i) => (
              <Tag
                key={i}
                tone="accent"
                removable
                onRemove={() => setAreas(areas.filter((_, j) => j !== i))}
              >
                {a}
              </Tag>
            ))}
          </div>
          <Input
            placeholder="Add a topic and press Enter"
            leadingIcon={<Plus size={16} style={{ color: 'var(--text-subtle)' }} />}
            onKeyDown={(e) => {
              const target = e.target as HTMLInputElement;
              if (e.key === 'Enter' && target.value.trim()) {
                setAreas([...areas, target.value.trim()]);
                target.value = '';
              }
            }}
          />
        </div>

        {sectionRule}

        <div style={{ marginBottom: '28px' }}>
          {monoHeader('Institution (optional)')}
          <p style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', color: 'var(--text-muted)', margin: '0 0 14px', maxWidth: '56ch' }}>
            Used for feasibility checks — e.g. live visa/mobility lookups for international candidates. Skipped when unset.
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: '14px' }}>
            <div>
              <label style={{ display: 'block', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', fontWeight: 500, color: 'var(--text-strong)', marginBottom: '6px' }}>
                University / institution
              </label>
              <input
                type="text"
                value={institution}
                onChange={e => setInstitution(e.target.value)}
                placeholder="e.g. Stanford University"
                style={{
                  width: '100%', boxSizing: 'border-box', padding: '0 12px', height: '40px',
                  fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)',
                  border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)',
                  background: 'var(--surface-card)', color: 'var(--text-body)', outline: 'none',
                }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', fontWeight: 500, color: 'var(--text-strong)', marginBottom: '6px' }}>
                Country
              </label>
              <input
                type="text"
                value={institutionCountry}
                onChange={e => setInstitutionCountry(e.target.value)}
                placeholder="e.g. United States"
                style={{
                  width: '100%', boxSizing: 'border-box', padding: '0 12px', height: '40px',
                  fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)',
                  border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)',
                  background: 'var(--surface-card)', color: 'var(--text-body)', outline: 'none',
                }}
              />
            </div>
          </div>
        </div>

        {sectionRule}

        <div style={{ marginBottom: '28px' }}>
          {monoHeader('Custom instructions to the review board')}
          <p style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', color: 'var(--text-muted)', margin: '0 0 12px', maxWidth: '56ch' }}>
            A free-text directive the agents follow when triaging and debating candidates — your standing preferences in plain English. Optional.
          </p>
          <textarea
            value={customInstructions}
            onChange={e => setCustomInstructions(e.target.value)}
            placeholder="e.g. I only take students with a strong theory background — deprioritise pure-applied ML. Prior publications matter more than GPA."
            rows={4}
            style={{
              width: '100%', boxSizing: 'border-box', padding: '12px',
              fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', lineHeight: '1.5',
              border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)',
              background: 'var(--surface-card)', color: 'var(--text-body)', outline: 'none',
              resize: 'vertical',
            }}
          />
        </div>

        {sectionRule}

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {monoHeader('Triage preferences')}
          <Checkbox
            label="Archive declines"
            description="When no claims verify and there is no research overlap, decline and archive it without asking you."
            checked={archiveDeclines}
            onChange={e => setArchiveDeclines(e.target.checked)}
          />
          <Checkbox
            label="Hold candidates when at capacity"
            description="Pause advancements automatically when all effective slots are filled."
            checked={holdAtCapacity}
            onChange={e => setHoldAtCapacity(e.target.checked)}
          />
        </div>
      </>
    );
  } else if (step === 2) {
    body = cardWrap(
      <>
        {monoHeader('Step 3 of 4')}
        {h2Title('Get outreach into Parallax')}
        {subDescription("Every professor gets a dedicated intake address. Share it with prospective students directly, or keep using your usual inbox and quietly forward matching mail — whichever fits how you already work.")}

        <div
          style={{
            display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '28px',
            padding: '14px 16px', borderRadius: 'var(--radius-lg)',
            background: 'var(--periwinkle-50)', border: '1px solid var(--periwinkle-100)',
          }}
        >
          <span style={{ flex: 1, minWidth: 0, fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--navy-900)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {intakeEmail || 'Generating your address…'}
          </span>
          <Button
            variant="secondary"
            size="sm"
            leadingIcon={intakeCopied ? <Check size={14} /> : <Copy size={14} />}
            onClick={() => {
              if (!intakeEmail) return;
              navigator.clipboard.writeText(intakeEmail);
              setIntakeCopied(true);
              setTimeout(() => setIntakeCopied(false), 2000);
            }}
            disabled={!intakeEmail}
          >
            {intakeCopied ? 'Copied' : 'Copy'}
          </Button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: '12px', marginBottom: '24px' }}>
          {(
            [
              { key: 'share' as const, icon: <Share2 size={18} />, title: 'Share it directly', copy: 'Post it on your lab page or hand it to students yourself. Nothing to configure.' },
              { key: 'forward' as const, icon: <Workflow size={18} />, title: 'Auto-forward from your inbox', copy: 'Keep your current email address. A quiet rule forwards matching mail here.' },
            ]
          ).map((opt) => {
            const active = intakeMode === opt.key;
            return (
              <button
                key={opt.key}
                type="button"
                onClick={() => setIntakeMode(opt.key)}
                style={{
                  textAlign: 'left', cursor: 'pointer', borderRadius: 'var(--radius-lg)',
                  padding: '16px', display: 'flex', flexDirection: 'column', gap: '8px',
                  border: `1.5px solid ${active ? 'var(--navy-900)' : 'var(--border-subtle)'}`,
                  background: active ? 'var(--surface-card)' : 'var(--surface-sunken)',
                  boxShadow: active ? 'var(--shadow-sm)' : 'none',
                  transition: 'border-color var(--duration-fast), background var(--duration-fast)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div
                    style={{
                      width: 32, height: 32, borderRadius: '999px', flexShrink: 0,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      background: active ? 'var(--navy-900)' : 'var(--surface-card)',
                      color: active ? 'var(--white)' : 'var(--text-muted)',
                      border: active ? 'none' : '1px solid var(--border-subtle)',
                    }}
                  >
                    {opt.icon}
                  </div>
                  <span style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-strong)' }}>
                    {opt.title}
                  </span>
                </div>
                <p style={{ margin: 0, fontFamily: 'var(--font-sans)', fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.45' }}>
                  {opt.copy}
                </p>
              </button>
            );
          })}
        </div>

        {intakeMode === 'share' ? (
          <div style={{ padding: '16px 18px', borderRadius: 'var(--radius-lg)', background: 'var(--status-verified-bg)', display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
            <CheckCircle size={16} style={{ color: 'var(--status-verified-ink)', flexShrink: 0, marginTop: '2px' }} />
            <p style={{ margin: 0, fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', color: 'var(--status-verified-ink)', lineHeight: '1.5' }}>
              You&apos;re all set — the address above is live. Add it to your lab page, syllabus, or reply template whenever you&apos;re ready.
            </p>
          </div>
        ) : (
          <>
            <div style={{ marginBottom: '20px' }}>
              {monoHeader('Setting up the forwarding rule')}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', color: 'var(--text-body)' }}>
                <div>
                  <strong style={{ display: 'block', marginBottom: '4px', color: 'var(--text-strong)' }}>Gmail / Google Workspace</strong>
                  <p style={{ margin: 0, color: 'var(--text-muted)', lineHeight: '1.4' }}>
                    Go to Settings → Filters and Blocked Addresses → Create a new filter. Set search term to look for keywords like <code>&quot;PhD student&quot;</code> or <code>&quot;prospective student&quot;</code>, and define the action to forward copy to your intake address.
                  </p>
                </div>
                <div>
                  <strong style={{ display: 'block', marginBottom: '4px', color: 'var(--text-strong)' }}>Outlook / Office 365</strong>
                  <p style={{ margin: 0, color: 'var(--text-muted)', lineHeight: '1.4' }}>
                    Go to Rules → Add new rule. Define a rule that forwards messages containing academic recruitment keywords directly to your unique intake address.
                  </p>
                </div>
              </div>
            </div>
          </>
        )}

        {sectionRule}

        <div>
          {monoHeader('Verify the pipeline')}
          <p style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', color: 'var(--text-muted)', margin: '0 0 16px', lineHeight: '1.4' }}>
            Send a synthetic test email to see the full triage, claim verification, and debate sequence play out — it&apos;ll show up in your queue either way.
          </p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
            <Button
              variant="secondary"
              onClick={handleTestIntake}
              disabled={testingIntake || !intakeEmail}
              leadingIcon={testingIntake ? <Loader size={14} style={{ animation: 'spin 1s linear infinite' }} /> : null}
            >
              {testingIntake ? 'Sending test email...' : 'Send test email'}
            </Button>
            {testIntakeSuccess && (
              <span style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-xs)', color: 'var(--status-verified-ink)', fontWeight: 500 }}>
                ✓ Synthetic email injected. It will appear in your inbox queue shortly!
              </span>
            )}
            {testIntakeError && (
              <span style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-xs)', color: 'var(--status-refuted-ink)', fontWeight: 500 }}>
                ⚠ {testIntakeError}
              </span>
            )}
          </div>
        </div>
      </>
    );
  } else {
    const effectiveSlots = Math.max(0, slots - committed);
    const fundingLabels: Record<string, string> = {
      department: 'Department',
      professor: 'Professor / grant',
      university: 'University / fellowship',
      mixed: 'Mixed sources'
    };
    const fundingLabel = fundingLabels[fundingSource] || '—';

    body = cardWrap(
      <>
        {monoHeader('Step 4 of 4')}
        {h2Title('Review your lab profile')}
        {subDescription('This is the ground truth every debate is measured against. You can update it any time from your lab profile — edits re-index and apply to subsequent outreach.')}

        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', gap: '14px', marginBottom: '16px' }}>
          {[
            { lbl: 'Publications indexed', val: indexed + ' of ' + papers.length },
            { lbl: 'Effective open slots', val: effectiveSlots },
            { lbl: 'Students committed', val: committed },
          ].map(({ lbl, val }) => (
            <div
              key={lbl}
              style={{ padding: '16px 18px', background: 'var(--surface-sunken)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)' }}
            >
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', letterSpacing: 'var(--tracking-caps)', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '6px' }}>
                {lbl}
              </div>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-display-md)', fontWeight: 600, color: 'var(--text-strong)' }}>
                {val}
              </div>
            </div>
          ))}
        </div>

        <div style={{ padding: '16px 18px', background: 'var(--surface-sunken)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)', marginBottom: '16px' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', letterSpacing: 'var(--tracking-caps)', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '4px' }}>
            Intake address
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-strong)' }}>
            {intakeEmail || '—'}
          </div>
        </div>

        <div style={{ padding: '16px 18px', background: 'var(--surface-sunken)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)', marginBottom: '16px', display: 'flex', gap: '32px' }}>
          <div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', letterSpacing: 'var(--tracking-caps)', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '4px' }}>
              Funding available
            </div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-display-md)', fontWeight: 600, color: 'var(--text-strong)' }}>
              {fundingAmount ? '$' + fundingAmount : '—'}
            </div>
          </div>
          <div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', letterSpacing: 'var(--tracking-caps)', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '4px' }}>
              Source
            </div>
            <div style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-md)', fontWeight: 600, color: 'var(--text-strong)', paddingTop: '4px' }}>
              {fundingLabel}
            </div>
          </div>
        </div>

        <div style={{ padding: '16px 18px', background: 'var(--surface-sunken)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)', marginBottom: '16px' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', letterSpacing: 'var(--tracking-caps)', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '10px' }}>
            Recruiting for
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {areas.map((a, i) => (
              <Tag key={i} tone="accent">
                {a}
              </Tag>
            ))}
          </div>
        </div>

        {needs.length > 0 && (
          <div
            style={{ padding: '14px 18px', background: 'var(--agent-3-bg)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--agent-3-bg)', display: 'flex', alignItems: 'flex-start', gap: '10px' }}
          >
            <AlertTriangle size={16} style={{ color: 'var(--agent-3-ink)', flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--agent-3-ink)', marginBottom: '2px' }}>
                {needs.length} paper{needs.length > 1 ? 's' : ''} could not be indexed
              </div>
              <div style={{ fontFamily: 'var(--font-sans)', fontSize: '12px', color: 'var(--agent-3-ink)', opacity: 0.8 }}>
                You can upload PDFs now or return to publications to resolve them.
              </div>
            </div>
          </div>
        )}
      </>
    );
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--surface-sunken)' }}>
      <header style={{ borderBottom: '1px solid var(--border-subtle)', background: 'var(--surface-card)' }}>
        <div style={{ maxWidth: 760, margin: '0 auto', padding: isMobile ? '14px 16px' : '18px 24px', display: 'flex', alignItems: 'center', gap: '10px' }}>
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
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)' }}>
            Lab setup
          </span>
        </div>
      </header>

      <div style={{ flex: 1, width: '100%', maxWidth: 760, margin: '0 auto', padding: isMobile ? '28px 16px 64px' : '44px 24px 80px', boxSizing: 'border-box' }}>
        <Stepper step={step} steps={STEPS} />
        {body}

        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '24px' }}>
          {step > 0 ? (
            <Button
              variant="ghost"
              leadingIcon={<ArrowLeft size={15} />}
              onClick={() => setStep(step - 1)}
              disabled={saving}
            >
              Back
            </Button>
          ) : (
            <span />
          )}

          {step < STEPS.length - 1 ? (
            <Button
              variant="primary"
              trailingIcon={<ArrowRight size={15} />}
              onClick={() => setStep(step + 1)}
            >
              Continue
            </Button>
          ) : (
            <Button
              variant="primary"
              trailingIcon={saving ? <Loader size={15} style={{ animation: 'spin 1s linear infinite' }} /> : <ArrowRight size={15} />}
              onClick={handleFinishSetup}
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Finish setup — open inbox'}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
