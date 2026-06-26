import { createClient } from '@supabase/supabase-js';

// Fallback placeholder values prevent createClient from throwing during
// Next.js build-time module evaluation. Real values must be set in .env.local.
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL ?? 'https://placeholder.supabase.co';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? 'placeholder-anon-key';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
