import React from 'react';

// Omit 'size' from HTMLInputElement to avoid conflict with our custom inputSize prop
interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: string;
  hint?: string;
  error?: string;
  inputSize?: 'sm' | 'md' | 'lg';
  leadingIcon?: React.ReactNode;
  containerStyle?: React.CSSProperties;
}

export function Input({
  label, hint, error, id, inputSize = 'md', leadingIcon = null,
  style = {}, containerStyle = {}, ...rest
}: InputProps) {
  const reactId = React.useId();
  const inputId = id || reactId;
  const [focused, setFocused] = React.useState(false);
  const heights: Record<string, string> = {
    sm: 'var(--control-sm)',
    md: 'var(--control-md)',
    lg: 'var(--control-lg)',
  };

  const fieldWrap: React.CSSProperties = {
    display: 'flex', alignItems: 'center', gap: '8px',
    height: heights[inputSize], padding: '0 12px',
    background: 'var(--surface-card)',
    border: `1px solid ${error ? 'var(--status-refuted)' : focused ? 'var(--focus-ring)' : 'var(--border-default)'}`,
    borderRadius: 'var(--radius-md)',
    boxShadow: focused ? 'var(--focus-shadow)' : 'none',
    transition: 'border-color var(--duration-fast) var(--ease-standard), box-shadow var(--duration-fast) var(--ease-standard)',
    boxSizing: 'border-box',
  };

  const inputStyle: React.CSSProperties = {
    flex: 1, border: 'none', outline: 'none', background: 'transparent',
    fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', color: 'var(--text-strong)',
    width: '100%', minWidth: 0, ...style,
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', ...containerStyle }}>
      {label && (
        <label htmlFor={inputId} style={{
          fontFamily: 'var(--font-sans)', fontSize: 'var(--text-xs)', fontWeight: 'var(--weight-medium)' as React.CSSProperties['fontWeight'],
          color: 'var(--text-body)',
        }}>{label}</label>
      )}
      <div style={fieldWrap}>
        {leadingIcon}
        <input id={inputId} style={inputStyle}
          onFocus={(e) => { setFocused(true); rest.onFocus?.(e); }}
          onBlur={(e) => { setFocused(false); rest.onBlur?.(e); }}
          {...rest} />
      </div>
      {(hint || error) && (
        <span style={{
          fontFamily: 'var(--font-sans)', fontSize: 'var(--text-xs)',
          color: error ? 'var(--status-refuted-ink)' : 'var(--text-muted)',
        }}>{error || hint}</span>
      )}
    </div>
  );
}
