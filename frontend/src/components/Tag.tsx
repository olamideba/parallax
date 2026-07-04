import React from 'react';

interface TagProps extends React.HTMLAttributes<HTMLSpanElement> {
  removable?: boolean;
  onRemove?: () => void;
  tone?: 'default' | 'accent' | 'muted';
}

export function Tag({ children, removable, onRemove, tone = 'default', style = {}, ...rest }: TagProps) {
  const tones = {
    default: { borderColor: 'var(--border-default)', color: 'var(--text-body)', background: 'var(--surface-card)' },
    accent:  { borderColor: 'var(--periwinkle-300)', color: 'var(--periwinkle-700)', background: 'var(--periwinkle-50)' },
    muted:   { borderColor: 'transparent', color: 'var(--text-muted)', background: 'var(--surface-muted)' },
  };
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '6px',
      padding: '3px 9px', borderRadius: 'var(--radius-sm)',
      border: `1px solid ${tones[tone].borderColor}`, background: tones[tone].background, color: tones[tone].color,
      fontFamily: 'var(--font-display)', fontSize: 'var(--text-xs)', fontWeight: 'var(--weight-regular)' as any,
      letterSpacing: 'var(--tracking-snug)', lineHeight: 1.4, whiteSpace: 'nowrap', ...style,
    }} {...rest}>
      {children}
      {removable && (
        <button type="button" onClick={onRemove} aria-label="Remove"
          style={{ display: 'inline-flex', border: 'none', background: 'none', padding: 0, cursor: 'pointer', color: 'inherit', opacity: 0.6 }}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            strokeWidth="2" strokeLinecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>
        </button>
      )}
    </span>
  );
}
