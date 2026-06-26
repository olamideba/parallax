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

export interface Outreach {
  id: string;
  professor_id: string;
  channel: string;
  sender_email: string;
  sender_name: string | null;
  subject: string | null;
  body: string;
  body_html: string | null;
  attachment_keys: string[];
  received_at: string;
  extracted_profile: ExtractedProfile | null;
  extracted_claims: ExtractedClaim[];
  triage_verdict: 'reject' | 'promote' | null;
  debate_trace_id: string | null;
  decision: Decision | null;
  status: 'pending_triage' | 'rejected' | 'awaiting_review' | 'replied';
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
}

export interface Publication {
  id: string;
  title: string;
  doi: string | null;
  url: string | null;
  indexed: boolean;
  storage_key: string | null;
}

export interface PublicationInput {
  title: string;
  doi: string | null;
  url: string | null;
}

async function getAuthHeaders(): Promise<HeadersInit> {
  const { data: { session } } = await supabase.auth.getSession();
  const token = session?.access_token;
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
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
    let errorDetail = 'API error occurred';
    try {
      const errorData = await res.json();
      errorDetail = errorData.detail || errorData.message || errorDetail;
    } catch {
      // Ignore
    }
    throw new Error(errorDetail);
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
  
  getReviewsQueue: (verdict?: 'promote' | 'reject') => {
    const query = verdict ? `?verdict=${verdict}` : '';
    return apiFetch<Outreach[]>(`/reviews/queue${query}`);
  },
  
  getReviewDetail: (id: string) => apiFetch<Outreach>(`/reviews/${id}`),
  
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
};
