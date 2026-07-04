import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'accent' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  leadingIcon?: React.ReactNode;
  trailingIcon?: React.ReactNode;
}

export function Button({
  variant = 'primary',
  size = 'md',
  disabled = false,
  fullWidth = false,
  type = 'button',
  leadingIcon = null,
  trailingIcon = null,
  children,
  style = {},
  ...rest
}: ButtonProps) {
  const sizes = {
    sm: { height: 'var(--control-sm)', padding: '0 12px', fontSize: 'var(--text-xs)', gap: '6px' },
    md: { height: 'var(--control-md)', padding: '0 16px', fontSize: 'var(--text-sm)', gap: '8px' },
    lg: { height: 'var(--control-lg)', padding: '0 22px', fontSize: 'var(--text-md)', gap: '8px' },
  };

  const variants = {
    primary: {
      background: 'var(--action)', color: 'var(--action-text)',
      border: '1px solid var(--action)',
    },
    accent: {
      background: 'var(--accent)', color: 'var(--white)',
      border: '1px solid var(--accent)',
    },
    secondary: {
      background: 'var(--surface-card)', color: 'var(--text-strong)',
      border: '1px solid var(--border-default)',
    },
    ghost: {
      background: 'transparent', color: 'var(--text-body)',
      border: '1px solid transparent',
    },
    danger: {
      background: 'var(--surface-card)', color: 'var(--status-refuted-ink)',
      border: '1px solid var(--border-default)',
    },
  };

  const base: React.CSSProperties = {
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
    fontFamily: 'var(--font-display)', fontWeight: 'var(--weight-medium)' as React.CSSProperties['fontWeight'],
    lineHeight: 1, letterSpacing: 'var(--tracking-snug)', borderRadius: 'var(--radius-md)',
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.45 : 1,
    width: fullWidth ? '100%' : 'auto',
    transition: 'background var(--duration-fast) var(--ease-standard), border-color var(--duration-fast) var(--ease-standard)',
    whiteSpace: 'nowrap', userSelect: 'none', boxSizing: 'border-box',
    ...sizes[size], ...variants[variant], ...style,
  };

  const hoverBg = {
    primary: 'var(--action-hover)', accent: 'var(--accent-hover)',
    secondary: 'var(--surface-muted)', ghost: 'var(--surface-muted)',
    danger: 'var(--status-refuted-bg)',
  };

  const [bg, setBg] = React.useState(variants[variant].background);

  // Sync background state when variant changes
  React.useEffect(() => {
    setBg(variants[variant].background);
  }, [variant]);

  const onEnter = () => { if (!disabled) setBg(hoverBg[variant]); };
  const onLeave = () => { if (!disabled) setBg(variants[variant].background); };

  return (
    <button
      type={type}
      disabled={disabled}
      style={{ ...base, background: bg }}
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
      {...rest}
    >
      {leadingIcon}
      {children}
      {trailingIcon}
    </button>
  );
}
