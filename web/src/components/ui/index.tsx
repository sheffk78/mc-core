import React from 'react';
import clsx from 'clsx';

// ── Badge ──

interface BadgeProps {
  variant?: 'default' | 'outline';
  className?: string;
  children: React.ReactNode;
}

export function Badge({ variant = 'default', className, children }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full px-2 py-0.5 text-[11px]',
        variant === 'default'
          ? 'border border-[var(--mc-border)] bg-black/5 text-[var(--mc-ink-muted)]'
          : 'border border-[var(--mc-border)] bg-transparent text-[var(--mc-ink-muted)]',
        className,
      )}
    >
      {children}
    </span>
  );
}

// ── Skeleton ──

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return <div className={clsx('animate-pulse rounded-md bg-black/5', className)} />;
}

// ── Button ──

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'ghost' | 'destructive';
  size?: 'sm' | 'md';
}

export function Button({
  variant = 'default',
  size = 'md',
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={clsx(
        'cursor-pointer rounded-lg font-medium transition-all duration-200 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50',
        size === 'md' ? 'px-4 py-2 text-sm' : 'px-3 py-1.5 text-xs',
        variant === 'default' && 'bg-[var(--mc-accent)] text-white hover:opacity-90',
        variant === 'ghost' &&
          'bg-transparent text-[var(--mc-ink-muted)] hover:bg-black/5 hover:text-[var(--mc-ink)]',
        variant === 'destructive' &&
          'bg-[var(--mc-red)]/20 text-[var(--mc-red)] hover:bg-[var(--mc-red)]/30',
        className,
      )}
      style={{ transitionTimingFunction: 'cubic-bezier(0.32, 0.72, 0, 1)' }}
      {...props}
    >
      {children}
    </button>
  );
}

// ── Input ──

export function Input({
  className,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={clsx(
        'rounded-lg border border-[var(--mc-border)] bg-[var(--mc-bg)] px-3 py-2 text-sm text-[var(--mc-ink)] placeholder:text-[var(--mc-ink-muted)] transition-colors duration-150 focus:border-[var(--mc-accent)] focus:outline-none',
        className,
      )}
      {...props}
    />
  );
}
