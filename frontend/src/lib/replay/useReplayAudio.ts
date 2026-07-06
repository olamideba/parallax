import { useEffect, useMemo, useRef } from 'react';
import { api, DebateTurn } from '@/lib/api';
import { Beat } from './timeline';

// The replay's clock stays authoritative: a single `playheadMs` drives every
// derived thing (active speaker, log, ledger) and every transport action
// (scrub / step / speed / seek) writes it directly. Audio is *slaved* to that
// clock rather than driving it. A turn with no audio simply plays as a silent
// beat; the clock keeps ticking regardless. This preserves the seekable-clock
// design — we don't introduce a second source of truth that could drift.
//
// Smoothness comes from per-turn buffering, not a single reused element:
//  - ONE <audio> element per turn, its `src` set once and never swapped, so the
//    browser buffers+decodes each clip independently and keeps it ready. Reusing
//    one element and re-`src`-ing it every turn (the old design) threw away the
//    decoded buffer each time and forced a fresh load/decode — that's the audible
//    break between turns.
//  - A rolling PRELOAD WINDOW (current + next 2) fetches and warms clips ahead of
//    the playhead so a turn is already decoded by the time it becomes active,
//    instead of racing the network at turn start.

// How many turns ahead of the active one to keep warmed.
const PRELOAD_AHEAD = 2;
// Keep a little slack behind too, so a small step-back doesn't reload.
const KEEP_BEHIND = 1;
// Re-seek the audio only when it has drifted past this from where the clock
// says it should be — avoids fighting normal playback with constant seeks.
const DRIFT_TOLERANCE_MS = 250;

interface WarmClip {
  url: string;
  audio: HTMLAudioElement;
}

interface UseReplayAudioArgs {
  reviewId: string;
  turns: DebateTurn[];
  beats: Beat[];
  activeIdx: number;
  playheadMs: number;
  playing: boolean;
  speed: number;
  /** Skip network fetches entirely (e.g. the demo fixture has no real audio). */
  enabled: boolean;
}

export function useReplayAudio({
  reviewId,
  turns,
  beats,
  activeIdx,
  playheadMs,
  playing,
  speed,
  enabled,
}: UseReplayAudioArgs): void {
  // index -> warmed clip (blob url + its own <audio> element). Absence means
  // "not warmed"; a value with url:'' means "fetched but this turn has no audio".
  const clipsRef = useRef<Map<number, WarmClip>>(new Map());
  // Turn indices whose fetch is in flight, so the window effect doesn't refetch.
  const inFlightRef = useRef<Set<number>>(new Set());

  // Which turns actually have audio to fetch.
  const audioTurns = useMemo(
    () => turns.map((t) => !!t.audio_key),
    [turns],
  );

  // Warm a rolling window [active - KEEP_BEHIND, active + PRELOAD_AHEAD]:
  // fetch each clip's blob and create its own preloaded <audio>. Release clips
  // that fall outside the window so memory stays bounded.
  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;

    const lo = Math.max(0, activeIdx - KEEP_BEHIND);
    const hi = Math.min(audioTurns.length - 1, activeIdx + PRELOAD_AHEAD);

    // Evict anything outside the window.
    for (const [i, clip] of clipsRef.current) {
      if (i < lo || i > hi) {
        clip.audio.pause();
        if (clip.url) URL.revokeObjectURL(clip.url);
        clipsRef.current.delete(i);
      }
    }

    const warm = async (i: number) => {
      if (i < 0 || i >= audioTurns.length) return;
      if (!audioTurns[i]) return; // this turn has no audio at all
      if (clipsRef.current.has(i) || inFlightRef.current.has(i)) return;
      inFlightRef.current.add(i);
      try {
        const url = await api.getTurnAudioUrl(reviewId, i);
        if (cancelled || url === null) return;
        // Blob is fully local now; give it a dedicated element and let the
        // browser decode it ahead of time so playback starts instantly.
        const audio = new Audio();
        audio.preload = 'auto';
        audio.src = url;
        audio.load();
        clipsRef.current.set(i, { url, audio });
      } catch {
        // leave unwarmed; the turn will play as a silent beat
      } finally {
        inFlightRef.current.delete(i);
      }
    };

    // Warm the active turn first, then look ahead.
    void warm(activeIdx);
    for (let i = activeIdx + 1; i <= hi; i++) void warm(i);

    return () => {
      cancelled = true;
    };
  }, [enabled, reviewId, activeIdx, audioTurns]);

  // Release every clip on unmount / trace change.
  useEffect(() => {
    const clips = clipsRef.current;
    const inFlight = inFlightRef.current;
    return () => {
      for (const clip of clips.values()) {
        clip.audio.pause();
        if (clip.url) URL.revokeObjectURL(clip.url);
      }
      clips.clear();
      inFlight.clear();
    };
  }, [reviewId]);

  // Drive ONLY the active turn's element; keep every other clip paused. No
  // element is ever re-`src`-ed, so each keeps its decoded buffer.
  useEffect(() => {
    if (!enabled) return;

    const active = clipsRef.current.get(activeIdx);
    const beat = activeIdx >= 0 ? beats[activeIdx] : null;

    // Pause any non-active clip that might still be playing (e.g. right after a
    // scrub/step changed the active turn).
    for (const [i, clip] of clipsRef.current) {
      if (i !== activeIdx && !clip.audio.paused) clip.audio.pause();
    }

    if (!active || !beat) return;

    const audio = active.audio;
    audio.playbackRate = speed;

    // Where the clock says we are within this turn's audio.
    const targetSec = Math.max(0, (playheadMs - beat.startMs) / 1000);
    // Only seek a clip that has enough buffered to seek into — seeking a still-
    // loading element restarts buffering and causes the break we're avoiding.
    const canSeek = audio.readyState >= 2; // HAVE_CURRENT_DATA
    if (
      canSeek &&
      Number.isFinite(audio.currentTime) &&
      Math.abs(audio.currentTime - targetSec) * 1000 > DRIFT_TOLERANCE_MS
    ) {
      try {
        audio.currentTime = targetSec;
      } catch {
        // Seeking before metadata loads throws; the next sync retries.
      }
    }

    if (playing && audio.paused) {
      void audio.play().catch(() => {
        // Autoplay can still be blocked until a gesture; the play CTA covers it.
      });
    } else if (!playing && !audio.paused) {
      audio.pause();
    }
  }, [enabled, activeIdx, beats, playheadMs, playing, speed]);
}
