import React from 'react';

interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  label?: string;
  description?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

export function Checkbox({
  label, description, checked, defaultChecked, disabled, id, onChange, style = {}, ...rest
}: CheckboxProps) {
  const reactId = React.useId();
  const cbId = id || reactId;
  const isControlled = checked !== undefined;
  const [internal, setInternal] = React.useState(!!defaultChecked);
  const on = isControlled ? checked : internal;

  const handle = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!isControlled) setInternal(e.target.checked);
    onChange?.(e);
  };

  return (
    <label htmlFor={cbId} style={{
      display: 'flex', alignItems: description ? 'flex-start' : 'center', gap: '10px',
      cursor: disabled ? 'not-allowed' : 'pointer', opacity: disabled ? 0.5 : 1, ...style,
    }}>
      <span style={{ position: 'relative', display: 'inline-flex', flexShrink: 0, marginTop: description ? '2px' : 0 }}>
        <input type="checkbox" id={cbId} checked={isControlled ? checked : undefined}
          defaultChecked={isControlled ? undefined : defaultChecked}
          disabled={disabled} onChange={handle}
          style={{ position: 'absolute', opacity: 0, width: 18, height: 18, margin: 0, cursor: 'inherit' }} {...rest} />
        <span aria-hidden style={{
          width: 18, height: 18, borderRadius: 'var(--radius-xs)',
          border: `1.5px solid ${on ? 'var(--action)' : 'var(--border-strong)'}`,
          background: on ? 'var(--action)' : 'var(--surface-card)',
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          transition: 'background var(--duration-fast), border-color var(--duration-fast)',
        }}>
          {on && (
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--white)"
              strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
          )}
        </span>
      </span>
      {(label || description) && (
        <span style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          {label && <span style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', color: 'var(--text-strong)', lineHeight: 1.4 }}>{label}</span>}
          {description && <span style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)', lineHeight: 1.4 }}>{description}</span>}
        </span>
      )}
    </label>
  );
}
