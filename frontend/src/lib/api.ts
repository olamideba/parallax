import { supabase } from './supabase';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface GlobalResponse<T> {
  success: boolean;
  data: T;
  message: string;
}

export interface ExtractedClaim {
  text: string;
  verified: boolean | null;
  receipt: string | null;
}

export interface ExtractedProfile {
  name: string | null;
  email: string | null;
  interests: string[];
  credentials: string[];
  funding_context: string | null;
  country: string | null;
}

export interface Decision {
  label: 'invite' | 'request_more_info' | 'decline';
  rationale: string;
  drafted_reply: string | null;
  overridden_by_professor: boolean;
}

// Mirrors backend/src/domain/models/society.py
export type AgentRole = 'gatekeeper' | 'advocate' | 'auditor' | 'assessor' | 'arbitrator';

export interface Receipt {
  source_title: string;
  chunk_text: string;
  relevance_note: string | null;
}

// How an agent reached for grounding during a turn (skill / MCP / RAG).
// Surfaced in the replay as tool chips so the engineering depth is visible.
export type ActionKind = 'skill' | 'mcp' | 'retrieval';

export interface AgentAction {
  kind: ActionKind;
  name: string;
  detail: string | null;
  source: string | null;   // MCP server id / skill id / index name
}

export interface DebateTurn {
  round: number;
  role: AgentRole;
  content: string;
  receipts: Receipt[];
  actions: AgentAction[];
  references_turn_ids: number[];   // indices of earlier turns this one builds on
  created_at: string;              // ISO timestamp
  // Filled in after the debate by the audio-synthesis step. `content` stays the
  // full evidentiary text; `spoken_line` is its short spoken rendering, and
  // `audio_duration_ms` is the real playback length that drives the replay clock
  // (absent/null → the replay falls back to a character-count heuristic beat).
  // Optional so fixtures/older traces without audio still satisfy the type.
  spoken_line?: string | null;
  audio_key?: string | null;
  audio_duration_ms?: number | null;
}

export interface DebateTrace {
  id: string;
  outreach_id: string;
  professor_id: string;
  turns: DebateTurn[];
  round_cap: number;
  terminated_at_round: number | null;
  started_at: string;
  ended_at: string | null;
}

export interface Attachment {
  storage_key: string;
  filename: string;
  content_type: string | null;
}

export interface Outreach {
  id: string;
  professor_id: string;
  channel: string;
  sender_email: string;
  sender_name: string | null;
  subject: string | null;
  body: string;
  body_html: string | null;
  attachment_keys: Attachment[];
  received_at: string;
  extracted_profile: ExtractedProfile | null;
  extracted_claims: ExtractedClaim[];
  triage_verdict: 'reject' | 'promote' | null;
  debate_trace_id: string | null;
  decision: Decision | null;
  status: 'pending_triage' | 'held' | 'rejected' | 'awaiting_review' | 'replied';
  replied_at: string | null;
}

export interface ProfessorProfile {
  id: string;
  email: string;
  display_name: string;
  intake_email: string;
  open_slots: number;
  students_committed: number;
  effective_open_slots: number;
  budget_amount: number | null;
  funding_source: string | null;
  recruiting_topics: string[];
  gatekeeper_aggressiveness: number;
  auto_resolve_declines: boolean;
  hold_when_at_capacity: boolean;
  custom_instructions: string | null;
  institution: string | null;
  institution_country: string | null;
}

export type PublicationStatus =
  | 'pending'       // queued, not yet picked up
  | 'indexing'      // Celery task running
  | 'indexed'       // text embedded in pgvector, ready for debate
  | 'needs_upload'  // DOI was paywalled, no OA PDF found
  | 'failed';       // ingestion error

export interface Publication {
  id: string;
  title: string | null;
  doi: string | null;
  url: string | null;
  indexed: boolean;
  status: PublicationStatus;   // authoritative field
  storage_key: string | null;
}

export interface PublicationInput {
  title: string | null;
  doi: string | null;
  url: string | null;
  storage_key: string | null;  // set after uploadPublicationPdf
}

export async function getAuthToken(): Promise<string | null> {
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}

async function getAuthHeaders(): Promise<HeadersInit> {
  const token = await getAuthToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

// Pull the human-readable error off a failed Response. The backend returns
// FastAPI's `{ detail }` on HTTPExceptions and our `{ message }` envelope on
// handled failures — reading both here means any new backend error message is
// surfaced by the frontend automatically, without a per-call change.
async function extractErrorDetail(res: Response, fallback: string): Promise<string> {
  try {
    const data = await res.json();
    return data.detail || data.message || fallback;
  } catch {
    return fallback;
  }
}

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = await getAuthHeaders();
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  
  // All api endpoints are prefixed: POST /api/v1/...
  const url = `${API_BASE}/api/v1${cleanEndpoint}`;

  const res = await fetch(url, {
    ...options,
    headers: {
      ...headers,
      ...options.headers,
    },
  });

  if (!res.ok) {
    throw new Error(await extractErrorDetail(res, 'API error occurred'));
  }

  const envelope = (await res.json()) as GlobalResponse<T>;
  if (!envelope.success) {
    throw new Error(envelope.message || 'API request returned success = false');
  }

  return envelope.data;
}

export const api = {
  getProfessorProfile: () => apiFetch<ProfessorProfile>('/professors/me'),
  
  patchProfessorProfile: (payload: Partial<Omit<ProfessorProfile, 'id' | 'email' | 'effective_open_slots'>>) => 
    apiFetch<ProfessorProfile>('/professors/me', {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  getPublications: () => apiFetch<Publication[]>('/professors/me/publications'),

  putPublications: (payload: PublicationInput[]) =>
    apiFetch<Publication[]>('/professors/me/publications', {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),

  uploadPublicationPdf: async (
    file: File,
    publicationId?: string,
  ): Promise<{ storage_key: string; publication: Publication | null }> => {
    const token = await getAuthToken();
    const form = new FormData();
    form.append('file', file);
    if (publicationId) form.append('publication_id', publicationId);

    const res = await fetch(`${API_BASE}/api/v1/professors/me/publications/upload`, {
      method: 'POST',
      // Do NOT set Content-Type — the browser sets it with the multipart boundary
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
    });

    if (!res.ok) {
      throw new Error(await extractErrorDetail(res, `Upload failed (${res.status})`));
    }
    const envelope = (await res.json()) as GlobalResponse<{
      storage_key: string;
      publication: Publication | null;
    }>;
    if (!envelope.success) throw new Error(envelope.message);
    return envelope.data;
  },

  addPublication: (payload: PublicationInput) =>
    apiFetch<Publication>('/professors/me/publications', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  addPublications: (payloads: PublicationInput[]) =>
    Promise.all(
      payloads.map((p) =>
        apiFetch<Publication>('/professors/me/publications', {
          method: 'POST',
          body: JSON.stringify(p),
        })
      )
    ),

  reingestPublication: (publicationId: string) =>
    apiFetch<Publication>(`/professors/me/publications/${publicationId}/ingest`, {
      method: 'POST',
    }),
  
  getReviewsQueue: (verdict?: 'promote' | 'reject') => {
    const query = verdict ? `?verdict=${verdict}` : '';
    return apiFetch<Outreach[]>(`/reviews/queue${query}`);
  },
  
  getReviewDetail: (id: string) => apiFetch<Outreach>(`/reviews/${id}`),

  // Fetches a stored attachment (auth header required) and returns a blob URL
  // the caller can open / revoke. Returns raw bytes, not the JSON envelope.
  getAttachmentUrl: async (id: string, index: number): Promise<string> => {
    const token = await getAuthToken();
    const res = await fetch(`${API_BASE}/api/v1/reviews/${id}/attachments/${index}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) {
      throw new Error(await extractErrorDetail(res, `Failed to load attachment (${res.status})`));
    }
    return URL.createObjectURL(await res.blob());
  },

  getDebateTrace: (id: string) => apiFetch<DebateTrace>(`/reviews/${id}/debate`),

  // Fetches one debate turn's synthesized speech (auth header required) and
  // returns a blob URL for an <audio> element, or null when the turn has no
  // audio (synthesis pending/failed) so the replay can fall back to a silent
  // heuristic beat. Returns raw bytes, not the JSON envelope.
  getTurnAudioUrl: async (id: string, index: number): Promise<string | null> => {
    const token = await getAuthToken();
    const res = await fetch(
      `${API_BASE}/api/v1/reviews/${id}/debate/turns/${index}/audio`,
      { headers: token ? { Authorization: `Bearer ${token}` } : {} },
    );
    if (res.status === 404) return null;
    if (!res.ok) {
      throw new Error(await extractErrorDetail(res, `Failed to load audio (${res.status})`));
    }
    return URL.createObjectURL(await res.blob());
  },
  
  approveDecision: (id: string) => apiFetch<Outreach>(`/reviews/${id}/approve`, {
    method: 'POST',
  }),
  
  overrideDecision: (id: string, payload: {
    label: 'invite' | 'request_more_info' | 'decline';
    rationale?: string;
    drafted_reply?: string | null;
  }) => apiFetch<Outreach>(`/reviews/${id}/override`, {
    method: 'POST',
    body: JSON.stringify(payload),
  }),

  testIntake: () => apiFetch<{ outreach_id: string; intake_email: string }>('/professors/me/intake/test', {
    method: 'POST',
  }),

  sendReply: (id: string, body: string) => apiFetch<Outreach>(`/reviews/${id}/reply`, {
    method: 'POST',
    body: JSON.stringify({ body }),
  }),

  retriageOutreach: (id: string) => apiFetch<Outreach>(`/reviews/${id}/retriage`, {
    method: 'POST',
  }),

  deleteOutreach: (id: string) => apiFetch<{ id: string }>(`/reviews/${id}`, {
    method: 'DELETE',
  }),
};
