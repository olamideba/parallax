import { useEffect, useMemo, useRef } from 'react';
import { api, DebateTurn } from '@/lib/api';
import { Beat } from './timeline';

// The replay's clock stays authoritative: a single `playheadMs` drives every
// derived thing (active speaker, log, ledger) and every transport action
// (scrub / step / speed / seek) writes it directly. Audio is *slaved* to that
// clock rather than driving it — one <audio> element per active turn is kept in
// sync with the playhead (play/pause, currentTime, playbackRate). A turn with
// no audio simply plays as a silent beat; the clock keeps ticking regardless.
//
// This preserves the seekable-clock design: we don't introduce a second source
// of truth that could drift from the playhead.

// Re-seek the audio only when it has drifted past this from where the clock
// says it should be — avoids fighting normal playback with constant seeks.
const DRIFT_TOLERANCE_MS = 250;

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
  const audioRef = useRef<HTMLAudioElement | null>(null);
  // Per-turn blob URLs (index → object URL), null once fetched-but-absent.
  const urlsRef = useRef<Map<number, string | null>>(new Map());
  // The turn index currently loaded into the <audio> element.
  const loadedIdxRef = useRef<number>(-1);

  // Create (and tear down) the single <audio> element off-render.
  useEffect(() => {
    const audio = new Audio();
    audio.preload = 'auto';
    audioRef.current = audio;
    return () => {
      audio.pause();
      audioRef.current = null;
    };
  }, []);

  // Which turns actually have audio to fetch.
  const audioTurns = useMemo(
    () => turns.map((t, i) => ({ i, has: !!t.audio_key })),
    [turns],
  );

  // Prefetch the active turn (and the next one) lazily as the playhead moves.
  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    const fetchFor = async (i: number) => {
      if (i < 0 || i >= audioTurns.length) return;
      if (!audioTurns[i].has) return;
      if (urlsRef.current.has(i)) return;
      urlsRef.current.set(i, null); // mark in-flight so we don't refetch
      try {
        const url = await api.getTurnAudioUrl(reviewId, i);
        if (!cancelled) urlsRef.current.set(i, url);
      } catch {
        if (!cancelled) urlsRef.current.set(i, null);
      }
    };
    void fetchFor(activeIdx);
    void fetchFor(activeIdx + 1);
    return () => {
      cancelled = true;
    };
  }, [enabled, reviewId, activeIdx, audioTurns]);

  // Revoke all blob URLs on unmount / trace change.
  useEffect(() => {
    const urls = urlsRef.current;
    return () => {
      for (const url of urls.values()) if (url) URL.revokeObjectURL(url);
      urls.clear();
      loadedIdxRef.current = -1;
    };
  }, [reviewId]);

  // Sync the <audio> to the playhead on every relevant change.
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !enabled) return;

    const beat = activeIdx >= 0 ? beats[activeIdx] : null;
    const url = urlsRef.current.get(activeIdx) ?? null;

    // No active audio-backed turn (before first beat, or synthesis absent):
    // ensure nothing is playing and let the clock run silently.
    if (!beat || !url) {
      if (!audio.paused) audio.pause();
      return;
    }

    // Load the right clip into the element when the active turn changes.
    if (loadedIdxRef.current !== activeIdx || audio.src !== url) {
      audio.src = url;
      loadedIdxRef.current = activeIdx;
    }

    audio.playbackRate = speed;

    // Where the clock says we are *within* this turn's audio.
    const targetSec = Math.max(0, (playheadMs - beat.startMs) / 1000);
    if (Number.isFinite(audio.currentTime) &&
        Math.abs(audio.currentTime - targetSec) * 1000 > DRIFT_TOLERANCE_MS) {
      try {
        audio.currentTime = targetSec;
      } catch {
        // Seeking before metadata loads throws; the next sync will retry.
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
