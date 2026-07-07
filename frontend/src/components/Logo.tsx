import React from 'react';

interface LogoProps {
  variant?: 'default' | 'on-dark' | 'mono-navy' | 'mono-white';
  size?: number;
  className?: string;
  style?: React.CSSProperties;
}

export function Logo({
  variant = 'default',
  size = 40,
  className = '',
  style = {},
}: LogoProps) {
  const stylesByVariant = {
    default: {
      '--c-wing-navy': '#061531',
      '--c-wing-peri': '#A1ABE8',
      '--c-circle-left': '#FFFFFF',
      '--c-circle-right': '#C8CFEE',
      '--c-dot-left': '#A1ABE8',
      '--c-dot-right': '#061531',
    },
    'on-dark': {
      '--c-wing-navy': '#A1ABE8',
      '--c-wing-peri': '#FEFEFE',
      '--c-circle-left': '#061531',
      '--c-circle-right': '#7B88D4',
      '--c-dot-left': '#FEFEFE',
      '--c-dot-right': '#061531',
    },
    'mono-navy': {
      '--c-wing-navy': '#061531',
      '--c-wing-peri': '#061531',
      '--c-circle-left': '#FEFEFE',
      '--c-circle-right': '#8E9ABF',
      '--c-dot-left': '#FEFEFE',
      '--c-dot-right': '#FEFEFE',
    },
    'mono-white': {
      '--c-wing-navy': '#FEFEFE',
      '--c-wing-peri': '#FEFEFE',
      '--c-circle-left': '#8E9ABF',
      '--c-circle-right': 'rgba(255,255,255,0.45)',
      '--c-dot-left': '#FEFEFE',
      '--c-dot-right': '#FEFEFE',
    },
  };

  const customVars = stylesByVariant[variant] as React.CSSProperties;

  return (
    <svg
      viewBox="0 0 80 80"
      width={size}
      height={size}
      className={className}
      style={{ ...customVars, ...style }}
    >
      <path
        d="M 40 26 L 14 20 A 6 6 0 0 0 8 26 L 8 54 A 6 6 0 0 0 14 60 L 40 54 A 14 14 0 1 0 40 26 Z"
        fill="var(--c-wing-navy, #061531)"
      />
      <path
        d="M 40 26 L 66 20 A 6 6 0 0 1 72 26 L 72 54 A 6 6 0 0 1 66 60 L 40 54 A 14 14 0 1 1 40 26 Z"
        fill="var(--c-wing-peri, #A1ABE8)"
      />
      <path d="M 40 26 A 14 14 0 1 0 40 54 Z" fill="var(--c-circle-left, #FFFFFF)" />
      <path d="M 40 26 A 14 14 0 1 1 40 54 Z" fill="var(--c-circle-right, #C8CFEE)" />
      <circle cx="20" cy="40" r="2.4" fill="var(--c-dot-left, #061531)" />
      <circle cx="60" cy="40" r="2.4" fill="var(--c-dot-right, #061531)" />
    </svg>
  );
}

interface WordmarkProps {
  variant?: 'default' | 'inverse' | 'periwinkle';
  size?: number;
  className?: string;
  style?: React.CSSProperties;
}

export function Wordmark({
  variant = 'default',
  size = 18,
  className = '',
  style = {},
}: WordmarkProps) {
  const colors = {
    default: 'var(--navy)',
    inverse: '#FEFEFE',
    periwinkle: 'var(--periwinkle)',
  };

  return (
    <div
      className={`wm ${className}`}
      style={{
        fontFamily: "var(--font-brand)",
        fontWeight: 700,
        letterSpacing: "0.12em",
        textTransform: "uppercase",
        color: colors[variant],
        fontSize: size,
        whiteSpace: "nowrap",
        lineHeight: 1,
        ...style,
      }}
    >
      PARALLAX
    </div>
  );
}
