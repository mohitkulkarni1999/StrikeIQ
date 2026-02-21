/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Trading Terminal Theme Colors
        background: '#0B0E11',
        card: '#14171C',
        border: '#2A2E39',
        text: {
          primary: '#E5E7EB',
          secondary: '#9CA3AF',
        },
        // Trading Signal Colors
        bullish: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22C55E', // Primary Bullish
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
        bearish: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#EF4444', // Primary Bearish
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
        },
        neutral: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#F59E0B', // Primary Neutral
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
        },
        // Expected Move / Analytics Blue
        analytics: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3B82F6', // Primary Analytics Blue
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        // Legacy color aliases for compatibility
        success: '#22C55E',
        danger: '#EF4444',
        warning: '#F59E0B',
        primary: '#3B82F6', // Changed from purple to analytics blue
        
        // Override default Tailwind purple colors with black/dark colors
        purple: {
          50: '#ffffff',
          100: '#f8fafc', 
          200: '#f1f5f9',
          300: '#e2e8f0',
          400: '#cbd5e1',
          500: '#94a3b8', // Light gray
          600: '#64748b', // Medium gray
          700: '#475569', // Dark gray
          800: '#1e293b', // Very dark
          900: '#0f172a', // Near black
          950: '#000000', // Pure black
        },
        
        // Override default Tailwind indigo colors with black/dark colors
        indigo: {
          50: '#ffffff',
          100: '#f8fafc',
          200: '#f1f5f9',
          300: '#e2e8f0',
          400: '#cbd5e1',
          500: '#94a3b8', // Light gray
          600: '#64748b', // Medium gray
          700: '#475569', // Dark gray
          800: '#1e293b', // Very dark
          900: '#0f172a', // Near black
          950: '#000000', // Pure black
        },
        
        // Override default Tailwind violet colors with black/dark colors
        violet: {
          50: '#ffffff',
          100: '#f8fafc',
          200: '#f1f5f9',
          300: '#e2e8f0',
          400: '#cbd5e1',
          500: '#94a3b8', // Light gray
          600: '#64748b', // Medium gray
          700: '#475569', // Dark gray
          800: '#1e293b', // Very dark
          900: '#0f172a', // Near black
          950: '#000000', // Pure black
        },
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-slow': 'bounce 2s infinite',
        'gradient': 'gradient 3s ease infinite',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'pulse-green': 'pulseGreen 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'pulse-red': 'pulseRed 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        gradient: {
          '0%, 100%': {
            backgroundPosition: '0% 50%',
          },
          '50%': {
            backgroundPosition: '100% 50%',
          },
        },
        slideUp: {
          '0%': {
            transform: 'translateY(10px)',
            opacity: '0',
          },
          '100%': {
            transform: 'translateY(0)',
            opacity: '1',
          },
        },
        slideDown: {
          '0%': {
            transform: 'translateY(-10px)',
            opacity: '0',
          },
          '100%': {
            transform: 'translateY(0)',
            opacity: '1',
          },
        },
        pulseGreen: {
          '0%, 100%': {
            backgroundColor: '#22C55E',
            boxShadow: '0 0 0 0 rgba(34, 197, 94, 0.7)',
          },
          '50%': {
            backgroundColor: '#22C55E',
            boxShadow: '0 0 0 10px rgba(34, 197, 94, 0)',
          },
        },
        pulseRed: {
          '0%, 100%': {
            backgroundColor: '#EF4444',
            boxShadow: '0 0 0 0 rgba(239, 68, 68, 0.7)',
          },
          '50%': {
            backgroundColor: '#EF4444',
            boxShadow: '0 0 0 10px rgba(239, 68, 68, 0)',
          },
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic':
          'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'trading-terminal': 'linear-gradient(135deg, #0B0E11 0%, #14171C 100%)',
      },
      // Trading terminal specific styles
      boxShadow: {
        'trading': '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2)',
        'trading-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.2)',
      },
      borderColor: {
        'trading': '#2A2E39',
        'bullish': '#22C55E',
        'bearish': '#EF4444',
        'neutral': '#F59E0B',
      },
    },
  },
  plugins: [],
};
