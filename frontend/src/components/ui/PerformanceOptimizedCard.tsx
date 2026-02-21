import React, { memo, useMemo, CSSProperties } from 'react';

interface PerformanceOptimizedCardProps {
  children: React.ReactNode;
  className?: string;
  style?: CSSProperties;
  // Performance props
  shouldUpdate?: boolean;
  dataKey?: string;
  // Layout props
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
  focusable?: boolean;
  // Accessibility props
  role?: string;
  'aria-label'?: string;
  'aria-describedby'?: string;
}

// Memoized card component with performance optimizations
const PerformanceOptimizedCard = memo(({
  children,
  className = '',
  style = {},
  shouldUpdate = true,
  dataKey,
  padding = 'md',
  hover = false,
  focusable = false,
  role = 'article',
  'aria-label': ariaLabel,
  'aria-describedby': ariaDescribedBy
}: PerformanceOptimizedCardProps) => {
  // Memoized padding styles to prevent recalculation
  const paddingStyles = useMemo(() => {
    switch (padding) {
      case 'none':
        return {};
      case 'sm':
        return { padding: '1rem' };
      case 'md':
        return { padding: '1.5rem' };
      case 'lg':
        return { padding: '2rem' };
      default:
        return { padding: '1.5rem' };
    }
  }, [padding]);

  // Memoized hover styles
  const hoverStyles = useMemo(() => {
    if (!hover) return {};
    return {
      transition: 'all 0.2s ease-in-out',
      cursor: 'pointer'
    };
  }, [hover]);

  // Memoized focus styles
  const focusStyles = useMemo(() => {
    if (!focusable) return {};
    return {
      outline: 'none',
      ':focus': {
        boxShadow: '0 0 0 2px #4F8CFF'
      }
    };
  }, [focusable]);

  // Combine all styles
  const combinedStyles = useMemo(() => ({
    backgroundColor: '#111827',
    border: '1px solid #1F2937',
    borderRadius: '0.75rem',
    ...paddingStyles,
    ...hoverStyles,
    ...focusStyles,
    ...style
  }), [paddingStyles, hoverStyles, focusStyles, style]);

  // Memoized class names
  const classNames = useMemo(() => {
    const baseClasses = [
      'performance-optimized-card',
      'bg-gray-900',
      'border-gray-800',
      'rounded-xl'
    ];

    if (hover) {
      baseClasses.push('hover:border-gray-600');
    }

    if (focusable) {
      baseClasses.push('focus:ring-2', 'focus:ring-blue-500', 'focus:ring-offset-2', 'focus:ring-offset-gray-900');
    }

    if (className) {
      baseClasses.push(className);
    }

    return baseClasses.join(' ');
  }, [hover, focusable, className]);

  // Performance optimization: skip render if shouldUpdate is false
  if (!shouldUpdate) {
    return null;
  }

  return (
    <div
      className={classNames}
      style={combinedStyles}
      role={role}
      aria-label={ariaLabel}
      aria-describedby={ariaDescribedBy}
      tabIndex={focusable ? 0 : undefined}
      data-key={dataKey}
    >
      {children}
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison function for performance
  // Only re-render if essential props change
  
  // Always re-render if shouldUpdate changes
  if (prevProps.shouldUpdate !== nextProps.shouldUpdate) {
    return false;
  }

  // Re-render if children change
  if (prevProps.children !== nextProps.children) {
    return false;
  }

  // Re-render if dataKey changes
  if (prevProps.dataKey !== nextProps.dataKey) {
    return false;
  }

  // Re-render if className changes
  if (prevProps.className !== nextProps.className) {
    return false;
  }

  // Re-render if style changes (deep comparison)
  if (JSON.stringify(prevProps.style) !== JSON.stringify(nextProps.style)) {
    return false;
  }

  // Skip re-render for other prop changes
  return true;
});

PerformanceOptimizedCard.displayName = 'PerformanceOptimizedCard';

export default PerformanceOptimizedCard;
