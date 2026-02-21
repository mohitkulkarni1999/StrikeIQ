import React, { memo, forwardRef } from 'react';
import { cn } from '../../utils/cn';

// Design system constants
export const COLORS = {
  primary: '#4F8CFF',
  success: '#00FF9F',
  danger: '#FF4D4F',
  warning: '#FFC857',
  info: '#4F8CFF',
  gray: {
    50: '#F9FAFB',
    100: '#F3F4F6',
    200: '#E5E7EB',
    300: '#D1D5DB',
    400: '#9CA3AF',
    500: '#6B7280',
    600: '#4B5563',
    700: '#374151',
    800: '#1F2937',
    900: '#111827',
  }
} as const;

export const SPACING = {
  xs: '0.25rem',
  sm: '0.5rem',
  md: '1rem',
  lg: '1.5rem',
  xl: '2rem',
  '2xl': '3rem',
  '3xl': '4rem',
} as const;

export const FONT_SIZES = {
  xs: '0.75rem',
  sm: '0.875rem',
  base: '1rem',
  lg: '1.125rem',
  xl: '1.25rem',
  '2xl': '1.5rem',
  '3xl': '1.875rem',
  '4xl': '2.25rem',
} as const;

export const BORDER_RADIUS = {
  sm: '0.25rem',
  md: '0.375rem',
  lg: '0.5rem',
  xl: '0.75rem',
  '2xl': '1rem',
  full: '9999px',
} as const;

// Base button component with performance optimizations
export const Button = memo(forwardRef<HTMLButtonElement, {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  disabled?: boolean;
  loading?: boolean;
  className?: string;
  children: React.ReactNode;
  onClick?: () => void;
  'aria-label'?: string;
}>(({
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  className = '',
  children,
  onClick,
  'aria-label': ariaLabel,
  ...props
}, ref) => {
  // Memoized variant styles to prevent recalculation
  const variantStyles = React.useMemo(() => {
    switch (variant) {
      case 'primary':
        return 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-2 focus:ring-blue-500';
      case 'secondary':
        return 'bg-gray-600 text-white hover:bg-gray-700 focus:ring-2 focus:ring-gray-500';
      case 'outline':
        return 'border border-gray-600 text-gray-300 hover:bg-gray-800 focus:ring-2 focus:ring-gray-500';
      case 'ghost':
        return 'text-gray-400 hover:text-white hover:bg-gray-800 focus:ring-2 focus:ring-gray-500';
      default:
        return 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-2 focus:ring-blue-500';
    }
  }, [variant]);

  // Memoized size styles
  const sizeStyles = React.useMemo(() => {
    switch (size) {
      case 'xs':
        return 'px-2 py-1 text-xs';
      case 'sm':
        return 'px-3 py-1.5 text-sm';
      case 'md':
        return 'px-4 py-2 text-sm';
      case 'lg':
        return 'px-6 py-3 text-base';
      case 'xl':
        return 'px-8 py-4 text-lg';
      default:
        return 'px-4 py-2 text-sm';
    }
  }, [size]);

  return (
    <button
      ref={ref}
      className={cn(
        // Base styles
        'inline-flex items-center justify-center font-medium rounded-md transition-colors duration-200',
        'focus:outline-none focus:ring-offset-2 focus:ring-offset-gray-900',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        
        // Variant and size styles
        variantStyles,
        sizeStyles,
        
        // Custom styles
        className
      )}
      disabled={disabled || loading}
      onClick={onClick}
      aria-label={ariaLabel}
      aria-busy={loading}
      {...props}
    >
      {loading && (
        <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
      )}
      {children}
    </button>
  );
}));

Button.displayName = 'Button';

// Card component with consistent styling
export const Card = memo(forwardRef<HTMLDivElement, {
  className?: string;
  children: React.ReactNode;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
}>(({
  className = '',
  children,
  padding = 'md',
  hover = false,
  ...props
}, ref) => {
  const paddingStyles = React.useMemo(() => {
    switch (padding) {
      case 'none':
        return '';
      case 'sm':
        return 'p-4';
      case 'md':
        return 'p-6';
      case 'lg':
        return 'p-8';
      default:
        return 'p-6';
    }
  }, [padding]);

  return (
    <div
      ref={ref}
      className={cn(
        'bg-[#111827] border border-[#1F2937] rounded-xl',
        paddingStyles,
        hover && 'hover:border-gray-600 transition-colors duration-200',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}));

Card.displayName = 'Card';

// Badge component for status indicators
export const Badge = memo(forwardRef<HTMLSpanElement, {
  variant?: 'success' | 'danger' | 'warning' | 'info' | 'gray';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  children: React.ReactNode;
}>(({
  variant = 'info',
  size = 'md',
  className = '',
  children,
  ...props
}, ref) => {
  const variantStyles = React.useMemo(() => {
    switch (variant) {
      case 'success':
        return 'bg-green-500/20 text-green-400 border-green-500/40';
      case 'danger':
        return 'bg-red-500/20 text-red-400 border-red-500/40';
      case 'warning':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40';
      case 'info':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/40';
      case 'gray':
        return 'bg-gray-500/20 text-gray-400 border-gray-500/40';
      default:
        return 'bg-blue-500/20 text-blue-400 border-blue-500/40';
    }
  }, [variant]);

  const sizeStyles = React.useMemo(() => {
    switch (size) {
      case 'sm':
        return 'px-2 py-0.5 text-xs';
      case 'md':
        return 'px-3 py-1 text-sm';
      case 'lg':
        return 'px-4 py-1.5 text-base';
      default:
        return 'px-3 py-1 text-sm';
    }
  }, [size]);

  return (
    <span
      ref={ref}
      className={cn(
        'inline-flex items-center justify-center font-medium rounded-full border',
        variantStyles,
        sizeStyles,
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}));

Badge.displayName = 'Badge';

// Loading spinner component
export const Spinner = memo(forwardRef<HTMLDivElement, {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}>(({
  size = 'md',
  className = '',
  ...props
}, ref) => {
  const sizeStyles = React.useMemo(() => {
    switch (size) {
      case 'xs':
        return 'w-3 h-3';
      case 'sm':
        return 'w-4 h-4';
      case 'md':
        return 'w-6 h-6';
      case 'lg':
        return 'w-8 h-8';
      case 'xl':
        return 'w-12 h-12';
      default:
        return 'w-6 h-6';
    }
  }, [size]);

  return (
    <div
      ref={ref}
      className={cn(
        'border-2 border-gray-700 border-t-gray-500 rounded-full animate-spin',
        sizeStyles,
        className
      )}
      role="status"
      aria-label="Loading"
      {...props}
    />
  );
}));

Spinner.displayName = 'Spinner';

// Metric display component for dashboard
export const Metric = memo(forwardRef<HTMLDivElement, {
  label: string;
  value: string | number;
  change?: number;
  changeType?: 'increase' | 'decrease' | 'neutral';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}>(({
  label,
  value,
  change,
  changeType = 'neutral',
  size = 'md',
  className = '',
  ...props
}, ref) => {
  const sizeStyles = React.useMemo(() => {
    switch (size) {
      case 'sm':
        return 'text-lg';
      case 'md':
        return 'text-2xl';
      case 'lg':
        return 'text-3xl';
      default:
        return 'text-2xl';
    }
  }, [size]);

  const changeColor = React.useMemo(() => {
    switch (changeType) {
      case 'increase':
        return 'text-green-400';
      case 'decrease':
        return 'text-red-400';
      case 'neutral':
        return 'text-gray-400';
      default:
        return 'text-gray-400';
    }
  }, [changeType]);

  return (
    <div ref={ref} className={cn('flex flex-col', className)} {...props}>
      <div className="text-xs text-gray-500 uppercase tracking-wider font-medium mb-1">
        {label}
      </div>
      <div className={cn('font-black text-white', sizeStyles)}>
        {value}
      </div>
      {change !== undefined && (
        <div className={cn('text-xs font-medium mt-1', changeColor)}>
          {changeType === 'increase' && '+'}
          {change}%
        </div>
      )}
    </div>
  );
}));

Metric.displayName = 'Metric';

// Grid system component
export const Grid = memo(forwardRef<HTMLDivElement, {
  cols?: 1 | 2 | 3 | 4 | 6 | 12;
  gap?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  children: React.ReactNode;
}>(({
  cols = 1,
  gap = 'md',
  className = '',
  children,
  ...props
}, ref) => {
  const colsStyles = React.useMemo(() => {
    switch (cols) {
      case 1:
        return 'grid-cols-1';
      case 2:
        return 'grid-cols-1 lg:grid-cols-2';
      case 3:
        return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3';
      case 4:
        return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4';
      case 6:
        return 'grid-cols-2 md:grid-cols-3 lg:grid-cols-6';
      case 12:
        return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-6';
      default:
        return 'grid-cols-1';
    }
  }, [cols]);

  const gapStyles = React.useMemo(() => {
    switch (gap) {
      case 'none':
        return 'gap-0';
      case 'sm':
        return 'gap-2';
      case 'md':
        return 'gap-4';
      case 'lg':
        return 'gap-6';
      case 'xl':
        return 'gap-8';
      default:
        return 'gap-4';
    }
  }, [gap]);

  return (
    <div
      ref={ref}
      className={cn('grid', colsStyles, gapStyles, className)}
      {...props}
    >
      {children}
    </div>
  );
}));

Grid.displayName = 'Grid';

// Container component for consistent max-width
export const Container = memo(forwardRef<HTMLDivElement, {
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  className?: string;
  children: React.ReactNode;
}>(({
  size = 'lg',
  className = '',
  children,
  ...props
}, ref) => {
  const sizeStyles = React.useMemo(() => {
    switch (size) {
      case 'sm':
        return 'max-w-2xl';
      case 'md':
        return 'max-w-4xl';
      case 'lg':
        return 'max-w-6xl';
      case 'xl':
        return 'max-w-7xl';
      case 'full':
        return 'max-w-full';
      default:
        return 'max-w-6xl';
    }
  }, [size]);

  return (
    <div
      ref={ref}
      className={cn('mx-auto px-4 sm:px-6 lg:px-8', sizeStyles, className)}
      {...props}
    >
      {children}
    </div>
  );
}));

Container.displayName = 'Container';
