'use client';

import { useEffect, useState } from 'react';

/**
 * Subscribe to a CSS media query. SSR-safe: returns `false` on the server and
 * on the first client render (so it matches the server-rendered markup), then
 * updates after mount. Inline styles can't hold media queries, so layout that
 * needs to respond to viewport width branches on this instead.
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const mql = window.matchMedia(query);
    const onChange = () => setMatches(mql.matches);
    onChange();
    mql.addEventListener('change', onChange);
    return () => mql.removeEventListener('change', onChange);
  }, [query]);

  return matches;
}

/** True on phone-sized viewports (single-column layouts). */
export function useIsMobile(): boolean {
  return useMediaQuery('(max-width: 768px)');
}
