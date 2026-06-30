import React from 'react';

interface LoaderProps {
  /** Rendered width in px. The GIF is 600x400, so height is derived to keep the 3:2 ratio. */
  width?: number;
  /** Optional caption shown under the animation. */
  label?: string;
  /** Fill the viewport and center the loader. Use for full-page loading states. */
  fullscreen?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export function Loader({
  width = 180,
  label,
  fullscreen = false,
  className = '',
  style = {},
}: LoaderProps) {
  const content = (
    <div
      className={className}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '12px',
        ...style,
      }}
    >
      {/* Plain <img> (not next/image) so the GIF animates without optimization stripping frames. */}
      <img
        src="/loading.gif"
        alt={label ?? 'Loading'}
        width={width}
        height={width * (400 / 600)}
        style={{ display: 'block' }}
      />
      {label && (
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 'var(--text-xs)',
            color: 'var(--text-muted)',
            letterSpacing: '0.05em',
          }}
        >
          {label}
        </span>
      )}
    </div>
  );

  if (!fullscreen) return content;

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: 'var(--surface-sunken)',
        padding: '24px',
      }}
    >
      {content}
    </div>
  );
}
