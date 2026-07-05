'use client';

export const dynamic = 'force-dynamic';

import React, { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';
import { api, ProfessorProfile, Publication, PublicationStatus } from '@/lib/api';
import { Logo, Wordmark } from '@/components/Logo';
import { Button } from '@/components/Button';
import { Input } from '@/components/Input';
import { Checkbox } from '@/components/Checkbox';
import { Tag } from '@/components/Tag';
import { Loader } from '@/components/Loader';
import { useIsMobile } from '@/lib/useMediaQuery';
import {
  ArrowLeft,
  BookOpen,
  Users,
  Mail,
  Check,
  CheckCircle,
  XCircle,
  Lock,
  Loader as LoaderIcon,
  Upload,
  Plus,
  LogOut,
  ShieldCheck,
} from 'lucide-react';

interface Paper {
  id: string;
  backendId: string;
  storageKey: string | null;
  title: string;
  doi: string;
  state: 'resolving' | 'indexed' | 'paywalled' | 'failed';
}

const statusToState = (s: PublicationStatus): Paper['state'] => ({
  pending: 'resolving',
  indexing: 'resolving',
  indexed: 'indexed',
  needs_upload: 'paywalled',
  failed: 'failed',
} as Record<PublicationStatus, Paper['state']>)[s] ?? 'failed';

const toPaper = (p: Publication): Paper => ({
  id: p.id,
  backendId: p.id,
  storageKey: p.storage_key,
  title: p.title ?? p.doi ?? p.url ?? '—',
  doi: p.doi ?? p.url ?? '',
  state: statusToState(p.status),
});

/* ── Shared section chrome ─────────────────────────────────────────────── */

function SectionCard({
  icon,
  title,
  description,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  const isMobile = useIsMobile();
  return (
    <section
      style={{
        background: 'var(--surface-card)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-xl)',
        boxShadow: 'var(--shadow-sm)',
        padding: isMobile ? '20px' : '28px 32px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', marginBottom: '24px' }}>
        <div style={{ width: 34, height: 34, borderRadius: 'var(--radius-md)', background: 'var(--periwinkle-50)', color: 'var(--navy-900)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          {icon}
        </div>
        <div style={{ minWidth: 0 }}>
          <h2 style={{ margin: '0 0 4px', fontFamily: 'var(--font-display)', fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--text-strong)', letterSpacing: '-0.01em' }}>
            {title}
          </h2>
          <p style={{ margin: 0, fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', color: 'var(--text-muted)', lineHeight: 1.5, maxWidth: '60ch' }}>
            {description}
          </p>
        </div>
      </div>
      {children}
    </section>
  );
}

function fieldLabel(t: string) {
  return (
    <label style={{ display: 'block', fontFamily: 'var(--font-display)', fontSize: '10px', fontWeight: 400, color: 'var(--text-muted)', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '8px' }}>
      {t}
    </label>
  );
}

function SaveBar({ dirty, saving, saved, onSave, onDiscard }: { dirty: boolean; saving: boolean; saved: boolean; onSave: () => void; onDiscard: () => void }) {
  if (!dirty && !saved) return null;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '24px', paddingTop: '20px', borderTop: '1px solid var(--border-subtle)' }}>
      {dirty ? (
        <>
          <Button variant="primary" size="sm" onClick={onSave} disabled={saving}>
            {saving ? 'Saving...' : 'Save changes'}
          </Button>
          <Button variant="ghost" size="sm" onClick={onDiscard} disabled={saving}>
            Discard
          </Button>
        </>
      ) : (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-xs)', color: 'var(--status-verified-ink)', fontWeight: 500 }}>
          <Check size={13} /> Saved
        </span>
      )}
    </div>
  );
}

function ResolutionPill({ state }: { state: Paper['state'] }) {
  const configs = {
    resolving: { label: 'Resolving…', color: 'var(--status-pending-ink)', bg: 'var(--status-pending-bg)', icon: <LoaderIcon size={12} style={{ animation: 'spin 1s linear infinite' }} /> },
    indexed: { label: 'Indexed', color: 'var(--status-verified-ink)', bg: 'var(--status-verified-bg)', icon: <CheckCircle size={12} /> },
    paywalled: { label: 'Needs PDF', color: 'var(--agent-3-ink)', bg: 'var(--agent-3-bg)', icon: <Lock size={12} /> },
    failed: { label: 'Not found', color: 'var(--status-refuted-ink)', bg: 'var(--status-refuted-bg)', icon: <XCircle size={12} /> },
  };
  const cfg = configs[state];
  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', padding: '3px 9px', borderRadius: '999px', background: cfg.bg, color: cfg.color, fontFamily: 'var(--font-sans)', fontSize: '11px', fontWeight: 500, whiteSpace: 'nowrap' }}>
      {cfg.icon}
      {cfg.label}
    </div>
  );
}

/* ── Publications section ──────────────────────────────────────────────── */

function PublicationsSection() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [doiText, setDoiText] = useState('');
  const [dropError, setDropError] = useState<string | null>(null);
  const [retryErrors, setRetryErrors] = useState<Record<string, string>>({});
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    api.getPublications().then((pubs) => {
      setPapers(pubs.map(toPaper));
      setLoaded(true);
    }).catch(() => setLoaded(true));
  }, []);

  // Poll while any paper is still resolving — same pattern as onboarding.
  useEffect(() => {
    const hasLive = papers.some((p) => p.state === 'resolving');
    if (!hasLive) return;
    const t = setInterval(async () => {
      try {
        const pubs = await api.getPublications();
        setPapers((prev) => prev.map((p) => {
          const fresh = pubs.find((q) => q.id === p.backendId);
          return fresh ? { ...p, title: fresh.title ?? p.title, state: statusToState(fresh.status), storageKey: fresh.storage_key ?? p.storageKey } : p;
        }));
      } catch {
        // ignore transient polling errors
      }
    }, 9000);
    return () => clearInterval(t);
  }, [papers]);

  const handleResolve = async () => {
    if (!doiText.trim()) return;
    const lines = doiText.trim().split(/\n+/).map((l) => l.trim()).filter(Boolean);
    setDoiText('');
    setDropError(null);
    const payloads = lines.map((line) => {
      const isUrl = line.startsWith('http://') || line.startsWith('https://');
      return { title: null, doi: isUrl ? null : line, url: isUrl ? line : null, storage_key: null };
    });
    try {
      const created = await api.addPublications(payloads);
      setPapers((prev) => [...prev, ...created.map(toPaper)]);
    } catch (err: unknown) {
      setDropError(err instanceof Error ? err.message : 'Failed to add publications');
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
      try {
        const { publication } = await api.uploadPublicationPdf(file);
        if (publication) setPapers((prev) => [...prev, toPaper(publication)]);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Upload failed';
        setDropError(msg.includes('25 MB') || msg.includes('413') ? 'File exceeds 25 MB limit' : msg.includes('415') || msg.includes('PDF') ? 'Only PDF files are supported' : msg);
      }
    }
  };

  const handleRetryUpload = async (paper: Paper, file: File) => {
    setRetryErrors((e) => ({ ...e, [paper.id]: '' }));
    setPapers((ps) => ps.map((p) => (p.id === paper.id ? { ...p, state: 'resolving' } : p)));
    try {
      await api.uploadPublicationPdf(file, paper.backendId);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed';
      setPapers((ps) => ps.map((p) => (p.id === paper.id ? { ...p, state: 'paywalled' as const } : p)));
      setRetryErrors((e) => ({ ...e, [paper.id]: msg }));
    }
  };

  const handleReingest = async (paper: Paper) => {
    setRetryErrors((e) => ({ ...e, [paper.id]: '' }));
    setPapers((ps) => ps.map((p) => (p.id === paper.id ? { ...p, state: 'resolving' } : p)));
    try {
      await api.reingestPublication(paper.backendId);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Retry failed';
      setPapers((ps) => ps.map((p) => (p.id === paper.id ? { ...p, state: 'failed' as const } : p)));
      setRetryErrors((e) => ({ ...e, [paper.id]: msg }));
    }
  };

  const indexed = papers.filter((p) => p.state === 'indexed').length;

  return (
    <SectionCard icon={<BookOpen size={17} />} title="Publications" description="The corpus every debate is grounded against — add papers any time and they're indexed and available to future outreach immediately.">
      <div
        style={{ border: '2px dashed var(--border-default)', borderRadius: 'var(--radius-lg)', padding: '24px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '8px', textAlign: 'center', background: 'var(--surface-sunken)', color: 'var(--text-muted)', marginBottom: dropError ? '8px' : '20px', cursor: 'pointer' }}
        onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
        onDrop={(e) => { e.preventDefault(); e.stopPropagation(); handlePdfFiles(Array.from(e.dataTransfer.files)); }}
        onClick={() => {
          const input = document.createElement('input');
          input.type = 'file';
          input.accept = '.pdf';
          input.multiple = true;
          input.onchange = () => { if (input.files) handlePdfFiles(Array.from(input.files)); };
          input.click();
        }}
      >
        <Upload size={18} style={{ color: 'var(--navy-900)' }} />
        <span style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-strong)' }}>
          Drop PDFs to add papers
        </span>
      </div>
      {dropError && (
        <div style={{ marginBottom: '16px', fontFamily: 'var(--font-sans)', fontSize: '12px', color: 'var(--status-refuted-ink)', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <XCircle size={13} />{dropError}
        </div>
      )}

      <div style={{ marginBottom: '20px' }}>
        {fieldLabel('or add by DOI / arXiv URL')}
        <textarea
          value={doiText}
          onChange={(e) => setDoiText(e.target.value)}
          placeholder="10.1145/3534678&#10;https://arxiv.org/abs/2205.01068"
          style={{ width: '100%', minHeight: 72, resize: 'vertical', boxSizing: 'border-box', fontFamily: 'var(--font-mono)', fontSize: '12px', lineHeight: 1.6, border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)', padding: '10px 12px', background: 'var(--surface-card)', color: 'var(--text-body)', outline: 'none' }}
        />
        <div style={{ marginTop: '8px', display: 'flex', justifyContent: 'flex-end' }}>
          <Button variant="secondary" size="sm" onClick={handleResolve} disabled={!doiText.trim()}>
            Resolve & index
          </Button>
        </div>
      </div>

      {!loaded ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '20px 0' }}>
          <Loader width={100} />
        </div>
      ) : papers.length > 0 ? (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <CheckCircle size={14} style={{ color: 'var(--status-verified)' }} />
            <span style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--status-verified-ink)' }}>
              {indexed} of {papers.length} indexed
            </span>
          </div>
          <div style={{ border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
            {papers.map((p, i) => (
              <div key={p.id} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '10px 14px', borderTop: i ? '1px solid var(--border-subtle)' : 'none', background: p.state === 'paywalled' ? 'var(--agent-3-bg)' : p.state === 'failed' ? 'var(--status-refuted-bg)' : 'transparent' }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-strong)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {p.title}
                  </div>
                </div>
                <ResolutionPill state={p.state} />
                {p.state === 'paywalled' && (
                  <>
                    <Button variant="ghost" style={{ padding: '4px 10px', fontSize: '12px' }} onClick={() => {
                      const input = document.createElement('input');
                      input.type = 'file';
                      input.accept = '.pdf';
                      input.onchange = (e) => {
                        const file = (e.target as HTMLInputElement).files?.[0];
                        if (file) handleRetryUpload(p, file);
                      };
                      input.click();
                    }}>
                      Upload PDF
                    </Button>
                    {retryErrors[p.id] && <span style={{ fontSize: '11px', color: 'var(--status-refuted-ink)' }}>{retryErrors[p.id]}</span>}
                  </>
                )}
                {p.state === 'failed' && (
                  <>
                    <Button variant="ghost" style={{ padding: '4px 10px', fontSize: '12px' }} onClick={() => handleReingest(p)}>
                      Retry
                    </Button>
                    {retryErrors[p.id] && <span style={{ fontSize: '11px', color: 'var(--status-refuted-ink)' }}>{retryErrors[p.id]}</span>}
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      ) : (
        <p style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', color: 'var(--text-subtle)', textAlign: 'center', padding: '16px 0', margin: 0 }}>
          No publications indexed yet.
        </p>
      )}
    </SectionCard>
  );
}

/* ── Lab capacity section ──────────────────────────────────────────────── */

function LabCapacitySection({ profile, onSaved }: { profile: ProfessorProfile; onSaved: (p: ProfessorProfile) => void }) {
  const isMobile = useIsMobile();
  const initial = {
    slots: profile.open_slots,
    committed: profile.students_committed,
    fundingAmount: profile.budget_amount ? String(profile.budget_amount) : '',
    fundingSource: profile.funding_source || '',
    areas: profile.recruiting_topics,
    archiveDeclines: profile.auto_resolve_declines,
    holdAtCapacity: profile.hold_when_at_capacity,
    customInstructions: profile.custom_instructions || '',
    institution: profile.institution || '',
    institutionCountry: profile.institution_country || '',
  };

  const [slots, setSlots] = useState(initial.slots);
  const [committed, setCommitted] = useState(initial.committed);
  const [fundingAmount, setFundingAmount] = useState(initial.fundingAmount);
  const [fundingSource, setFundingSource] = useState(initial.fundingSource);
  const [areas, setAreas] = useState(initial.areas);
  const [archiveDeclines, setArchiveDeclines] = useState(initial.archiveDeclines);
  const [holdAtCapacity, setHoldAtCapacity] = useState(initial.holdAtCapacity);
  const [customInstructions, setCustomInstructions] = useState(initial.customInstructions);
  const [institution, setInstitution] = useState(initial.institution);
  const [institutionCountry, setInstitutionCountry] = useState(initial.institutionCountry);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const dirty =
    slots !== initial.slots ||
    committed !== initial.committed ||
    fundingAmount !== initial.fundingAmount ||
    fundingSource !== initial.fundingSource ||
    JSON.stringify(areas) !== JSON.stringify(initial.areas) ||
    archiveDeclines !== initial.archiveDeclines ||
    holdAtCapacity !== initial.holdAtCapacity ||
    customInstructions !== initial.customInstructions ||
    institution !== initial.institution ||
    institutionCountry !== initial.institutionCountry;

  const discard = () => {
    setSlots(initial.slots);
    setCommitted(initial.committed);
    setFundingAmount(initial.fundingAmount);
    setFundingSource(initial.fundingSource);
    setAreas(initial.areas);
    setArchiveDeclines(initial.archiveDeclines);
    setHoldAtCapacity(initial.holdAtCapacity);
    setCustomInstructions(initial.customInstructions);
    setInstitution(initial.institution);
    setInstitutionCountry(initial.institutionCountry);
    setSaved(false);
  };

  const save = async () => {
    setSaving(true);
    try {
      const updated = await api.patchProfessorProfile({
        open_slots: slots,
        students_committed: committed,
        budget_amount: parseInt(fundingAmount.replace(/,/g, '')) || null,
        funding_source: fundingSource || null,
        recruiting_topics: areas,
        auto_resolve_declines: archiveDeclines,
        hold_when_at_capacity: holdAtCapacity,
        custom_instructions: customInstructions.trim() || null,
        institution: institution.trim() || null,
        institution_country: institutionCountry.trim() || null,
      });
      onSaved(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } finally {
      setSaving(false);
    }
  };

  return (
    <SectionCard icon={<Users size={17} />} title="Lab capacity" description="Agents weigh every candidate against these constraints. Capacity is a hard signal, not a guess — keep it current as slots fill.">
      <div style={{ marginBottom: '24px' }}>
        {fieldLabel('Open student slots this cycle')}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {[0, 1, 2, 3, 4, 5].map((n) => (
            <button key={n} onClick={() => setSlots(n)} style={{ width: 40, height: 40, borderRadius: 'var(--radius-md)', cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-md)', fontWeight: 600, border: '1px solid ' + (slots === n ? 'var(--navy-900)' : 'var(--border-default)'), background: slots === n ? 'var(--navy-900)' : 'var(--surface-card)', color: slots === n ? 'var(--white)' : 'var(--text-body)' }}>
              {n}
            </button>
          ))}
        </div>
      </div>

      <div style={{ marginBottom: '24px' }}>
        {fieldLabel('Students already committed')}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {[0, 1, 2, 3, 4].map((n) => (
            <button key={n} onClick={() => setCommitted(n)} style={{ width: 40, height: 40, borderRadius: 'var(--radius-md)', cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-md)', fontWeight: 600, border: '1px solid ' + (committed === n ? 'var(--periwinkle-700)' : 'var(--border-default)'), background: committed === n ? 'var(--periwinkle-100)' : 'var(--surface-card)', color: committed === n ? 'var(--periwinkle-700)' : 'var(--text-body)' }}>
              {n}
            </button>
          ))}
        </div>
        <p style={{ fontFamily: 'var(--font-sans)', fontSize: '12px', color: 'var(--text-subtle)', margin: '8px 0 0' }}>
          {Math.max(0, slots - committed)} effective open slot{Math.max(0, slots - committed) !== 1 ? 's' : ''}
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: '14px', marginBottom: '24px' }}>
        <div>
          {fieldLabel('Available budget (USD/yr)')}
          <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
            <span style={{ position: 'absolute', left: 12, fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)', color: 'var(--text-muted)', pointerEvents: 'none' }}>$</span>
            <input type="text" value={fundingAmount} onChange={(e) => setFundingAmount(e.target.value)} placeholder="40,000" style={{ width: '100%', boxSizing: 'border-box', paddingLeft: '26px', paddingRight: '12px', height: '40px', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)', background: 'var(--surface-card)', color: 'var(--text-body)', outline: 'none' }} />
          </div>
        </div>
        <div>
          {fieldLabel('Funding source')}
          <select value={fundingSource} onChange={(e) => setFundingSource(e.target.value)} style={{ width: '100%', height: '40px', boxSizing: 'border-box', padding: '0 12px', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)', background: 'var(--surface-card)', color: fundingSource ? 'var(--text-body)' : 'var(--text-subtle)', outline: 'none' }}>
            <option value="" disabled>Select source</option>
            <option value="department">Department funding</option>
            <option value="professor">Professor / grant funding</option>
            <option value="university">University / fellowship</option>
            <option value="mixed">Mixed sources</option>
          </select>
        </div>
      </div>

      <div style={{ marginBottom: '24px' }}>
        {fieldLabel('Projects and topics currently recruiting for')}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '12px' }}>
          {areas.map((a, i) => (
            <Tag key={i} tone="accent" removable onRemove={() => setAreas(areas.filter((_, j) => j !== i))}>
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

      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: '14px', marginBottom: '24px' }}>
        <div>
          {fieldLabel('University / institution (optional)')}
          <input type="text" value={institution} onChange={(e) => setInstitution(e.target.value)} placeholder="e.g. Stanford University" style={{ width: '100%', boxSizing: 'border-box', padding: '0 12px', height: '40px', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)', background: 'var(--surface-card)', color: 'var(--text-body)', outline: 'none' }} />
        </div>
        <div>
          {fieldLabel('Country')}
          <input type="text" value={institutionCountry} onChange={(e) => setInstitutionCountry(e.target.value)} placeholder="e.g. United States" style={{ width: '100%', boxSizing: 'border-box', padding: '0 12px', height: '40px', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)', background: 'var(--surface-card)', color: 'var(--text-body)', outline: 'none' }} />
        </div>
      </div>

      <div style={{ marginBottom: '24px' }}>
        {fieldLabel('Custom instructions to the review board')}
        <textarea
          value={customInstructions}
          onChange={(e) => setCustomInstructions(e.target.value)}
          placeholder="e.g. I only take students with a strong theory background."
          rows={3}
          style={{ width: '100%', boxSizing: 'border-box', padding: '12px', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', lineHeight: '1.5', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)', background: 'var(--surface-card)', color: 'var(--text-body)', outline: 'none', resize: 'vertical' }}
        />
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {fieldLabel('Triage preferences')}
        <Checkbox label="Archive declines" description="When no claims verify and there is no research overlap, decline and archive it without asking you." checked={archiveDeclines} onChange={(e) => setArchiveDeclines(e.target.checked)} />
        <Checkbox label="Hold candidates when at capacity" description="Pause advancements automatically when all effective slots are filled." checked={holdAtCapacity} onChange={(e) => setHoldAtCapacity(e.target.checked)} />
      </div>

      <SaveBar dirty={dirty} saving={saving} saved={saved} onSave={save} onDiscard={discard} />
    </SectionCard>
  );
}

/* ── Email forwarding section ──────────────────────────────────────────── */

function EmailForwardingSection({ intakeEmail }: { intakeEmail: string }) {
  const [testing, setTesting] = useState(false);
  const [testSuccess, setTestSuccess] = useState(false);
  const [testError, setTestError] = useState<string | null>(null);

  const handleTest = async () => {
    setTesting(true);
    setTestSuccess(false);
    setTestError(null);
    try {
      await api.testIntake();
      setTestSuccess(true);
    } catch (err: unknown) {
      setTestError(err instanceof Error ? err.message : 'Failed to inject test email.');
    } finally {
      setTesting(false);
    }
  };

  return (
    <SectionCard icon={<Mail size={17} />} title="Email forwarding" description="Qualifying incoming cold emails must be forwarded here so debate agents can triage, index, and draft replies for your review.">
      <div style={{ marginBottom: '20px' }}>
        {fieldLabel('Your unique Parallax intake address')}
        <div style={{ display: 'flex', gap: '8px' }}>
          <input type="text" readOnly value={intakeEmail || 'Generating address...'} style={{ flex: 1, height: '40px', boxSizing: 'border-box', padding: '0 12px', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)', background: 'var(--surface-sunken)', color: 'var(--text-strong)', outline: 'none' }} />
          <Button variant="secondary" onClick={() => { if (intakeEmail) navigator.clipboard.writeText(intakeEmail); }} disabled={!intakeEmail}>
            Copy
          </Button>
        </div>
      </div>

      <div>
        {fieldLabel('Verify the pipeline')}
        <p style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', color: 'var(--text-muted)', margin: '0 0 14px', lineHeight: '1.4' }}>
          Send a synthetic test email through the complete triage, claim verification, and debate sequence — it will show up in your queue.
        </p>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
          <Button variant="secondary" size="sm" onClick={handleTest} disabled={testing || !intakeEmail} leadingIcon={testing ? <LoaderIcon size={13} style={{ animation: 'spin 1s linear infinite' }} /> : null}>
            {testing ? 'Sending test email...' : 'Send test email'}
          </Button>
          {testSuccess && <span style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-xs)', color: 'var(--status-verified-ink)', fontWeight: 500 }}>Synthetic email injected — check your inbox queue.</span>}
          {testError && <span style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-xs)', color: 'var(--status-refuted-ink)', fontWeight: 500 }}>{testError}</span>}
        </div>
      </div>
    </SectionCard>
  );
}

/* ── Security section ──────────────────────────────────────────────────── */

function SecuritySection({ email }: { email: string }) {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const dirty = currentPassword.length > 0 || newPassword.length > 0 || confirmPassword.length > 0;

  const discard = () => {
    setCurrentPassword('');
    setNewPassword('');
    setConfirmPassword('');
    setError(null);
    setSaved(false);
  };

  const handleSubmit = async () => {
    setError(null);

    if (newPassword.length < 8) {
      setError('New password must be at least 8 characters.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('New passwords do not match.');
      return;
    }

    setSaving(true);
    try {
      // updateUser() alone would accept this on the strength of the current
      // session — re-verifying the current password first confirms it's
      // really the account owner, not just whoever has the browser open.
      const { error: reauthError } = await supabase.auth.signInWithPassword({ email, password: currentPassword });
      if (reauthError) {
        setError('Current password is incorrect.');
        return;
      }

      const { error: updateError } = await supabase.auth.updateUser({ password: newPassword });
      if (updateError) {
        setError(updateError.message);
        return;
      }

      discard();
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } finally {
      setSaving(false);
    }
  };

  return (
    <SectionCard icon={<ShieldCheck size={17} />} title="Security" description="Change the password used to sign in to Parallax.">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {error && (
          <div style={{ padding: '10px 12px', background: 'var(--status-refuted-bg)', border: '1px solid var(--status-refuted-ink)', borderRadius: 'var(--radius-md)', color: 'var(--status-refuted-ink)', fontSize: 'var(--text-xs)', fontFamily: 'var(--font-sans)', lineHeight: 1.4 }}>
            {error}
          </div>
        )}
        <Input
          label="Current password"
          type="password"
          placeholder="••••••••"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          disabled={saving}
          autoComplete="current-password"
        />
        <Input
          label="New password"
          type="password"
          placeholder="••••••••"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          disabled={saving}
          hint="At least 8 characters."
          autoComplete="new-password"
        />
        <Input
          label="Confirm new password"
          type="password"
          placeholder="••••••••"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          disabled={saving}
          autoComplete="new-password"
        />
        <SaveBar
          dirty={dirty && !!currentPassword && !!newPassword && !!confirmPassword}
          saving={saving}
          saved={saved}
          onSave={handleSubmit}
          onDiscard={discard}
        />
      </div>
    </SectionCard>
  );
}

/* ── Page ───────────────────────────────────────────────────────────────── */

export default function SettingsPage() {
  const router = useRouter();
  const isMobile = useIsMobile();
  const userIdRef = useRef<string | null>(null);

  const [displayName, setDisplayName] = useState('');
  const [profile, setProfile] = useState<ProfessorProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadProfile = async () => {
    try {
      setError(null);
      const prof = await api.getProfessorProfile();
      setProfile(prof);
      setDisplayName(prof.display_name);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load lab profile.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const applySession = (session: NonNullable<Awaited<ReturnType<typeof supabase.auth.getSession>>['data']['session']>) => {
      const isNewUser = session.user.id !== userIdRef.current;
      userIdRef.current = session.user.id;
      setDisplayName(session.user.user_metadata?.display_name || 'Dr. Professor');
      return isNewUser;
    };

    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        applySession(session);
        loadProfile();
      } else {
        router.push('/login');
      }
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (session) {
        const isNewUser = applySession(session);
        if (isNewUser) loadProfile();
      } else {
        router.push('/login');
      }
    });

    return () => subscription.unsubscribe();
  }, [router]);

  const handleSignout = async () => {
    await supabase.auth.signOut();
    router.push('/login');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--surface-sunken)' }}>
      <header style={{ borderBottom: '1px solid var(--border-subtle)', background: 'var(--surface-card)' }}>
        <div style={{ maxWidth: '880px', margin: '0 auto', padding: isMobile ? '14px 16px' : '18px 24px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: 30, height: 30, borderRadius: '7px', background: '#FEFEFE', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, boxShadow: '0 1px 3px rgba(0,0,0,0.12)' }}>
            <Logo size={22} />
          </div>
          <Wordmark size={18} />
          <span style={{ flex: 1 }} />
          <span style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-sm)', color: 'var(--text-strong)', fontWeight: 400, letterSpacing: 'var(--tracking-snug)' }}>
            {displayName}
          </span>
          <button onClick={handleSignout} title="Sign out" style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', alignItems: 'center', padding: '6px', borderRadius: 'var(--radius-sm)' }}>
            <LogOut size={16} />
          </button>
        </div>
      </header>

      <main style={{ flex: 1, width: '100%', maxWidth: '880px', margin: '0 auto', padding: isMobile ? '28px 16px 64px' : '44px 24px 80px', boxSizing: 'border-box' }}>
        <Link href="/inbox" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', textDecoration: 'none', color: 'var(--text-muted)', fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', marginBottom: '20px' }}>
          <ArrowLeft size={16} />
          Back to inbox
        </Link>

        <div style={{ marginBottom: '32px' }}>
          <span style={{ fontFamily: 'var(--font-display)', fontSize: '10px', fontWeight: 400, color: 'var(--text-muted)', letterSpacing: 'var(--tracking-caps)', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>
            Lab profile
          </span>
          <h1 style={{ margin: 0, fontFamily: 'var(--font-display)', fontSize: 'var(--text-display-md)', fontWeight: 700, color: 'var(--text-strong)', letterSpacing: '-0.01em' }}>
            Settings
          </h1>
        </div>

        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '80px 0' }}>
            <Loader width={140} label="Loading lab profile..." />
          </div>
        ) : error || !profile ? (
          <div style={{ background: 'var(--surface-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-xl)', padding: '32px', textAlign: 'center' }}>
            <p style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', color: 'var(--status-refuted-ink)', margin: '0 0 16px' }}>{error || 'Could not load profile.'}</p>
            <Button variant="primary" onClick={loadProfile}>Retry</Button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <PublicationsSection />
            <LabCapacitySection profile={profile} onSaved={setProfile} />
            <EmailForwardingSection intakeEmail={profile.intake_email} />
            <SecuritySection email={profile.email} />
          </div>
        )}
      </main>
    </div>
  );
}
