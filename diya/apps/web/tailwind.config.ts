import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        diya: {
          bg: '#000000',
          surface: '#0a0a0a',
          card: '#111111',
          'card-hover': '#141414',
          border: '#1a1a1a',
          'border-light': '#222222',
          'border-hover': '#333333',
          text: '#ffffff',
          'text-secondary': '#a0a0a0',
          'text-muted': '#666666',
          accent: '#ffffff',
          'accent-dim': '#888888',
          // Status colors - used sparingly
          conflict: '#ef4444',
          'conflict-dim': 'rgba(239, 68, 68, 0.15)',
          resolved: '#22c55e',
          'resolved-dim': 'rgba(34, 197, 94, 0.15)',
          pending: '#f59e0b',
          'pending-dim': 'rgba(245, 158, 11, 0.15)',
          info: '#3b82f6',
          'info-dim': 'rgba(59, 130, 246, 0.15)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-right': 'slideRight 0.3s ease-out',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideRight: {
          '0%': { opacity: '0', transform: 'translateX(-10px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(255, 255, 255, 0.1)' },
          '100%': { boxShadow: '0 0 20px rgba(255, 255, 255, 0.05)' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
};

export default config;
