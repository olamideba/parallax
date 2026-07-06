import React from 'react';

/* lucide-react v1 dropped brand marks (no Github export) — this is the
   actual GitHub octocat glyph, not a generic substitute. currentColor so it
   inherits whatever color context it's dropped into. */
export function GithubIcon({ size = 18, className, style }: { size?: number; className?: string; style?: React.CSSProperties }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      fill="currentColor"
      className={className}
      style={style}
      aria-hidden="true"
    >
      <path d="M12 .5C5.73.5.5 5.73.5 12c0 5.08 3.29 9.39 7.86 10.91.57.1.78-.25.78-.55 0-.27-.01-1.17-.02-2.12-3.2.7-3.88-1.36-3.88-1.36-.52-1.33-1.28-1.68-1.28-1.68-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.18 1.76 1.18 1.03 1.75 2.69 1.25 3.35.95.1-.75.4-1.25.73-1.54-2.56-.29-5.25-1.28-5.25-5.71 0-1.26.45-2.29 1.18-3.09-.12-.29-.51-1.47.11-3.06 0 0 .97-.31 3.18 1.18a11 11 0 0 1 2.9-.39c.98.01 1.97.13 2.9.39 2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.24 2.77.12 3.06.74.8 1.18 1.83 1.18 3.09 0 4.44-2.7 5.42-5.27 5.7.41.36.78 1.07.78 2.15 0 1.55-.01 2.8-.01 3.18 0 .3.2.66.79.55A10.51 10.51 0 0 0 23.5 12C23.5 5.73 18.27.5 12 .5Z" />
    </svg>
  );
}
