/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Repointed to the AUVI Z.ai oklch palette (purple → magenta → orange).
        // Token names are unchanged so existing markup inherits the new look.
        base: 'oklch(0.13 0.012 285)',
        surface: 'oklch(0.15 0.013 285)',
        card: 'oklch(0.17 0.015 285)',
        'card-hover': 'oklch(0.21 0.02 285)',
        accent: {
          1: 'oklch(0.62 0.24 320)',   // primary purple
          2: 'oklch(0.7 0.2 350)',     // magenta
          glow: 'oklch(0.62 0.24 320)',
        },
        'text-primary': 'oklch(0.97 0.005 285)',
        'text-muted': 'oklch(0.65 0.02 285)',
        'text-hint': 'oklch(0.45 0.015 285)',
        border: 'oklch(0.27 0.015 285 / 60%)',
        success: '#10B981',
        warning: '#F59E0B',
        danger: '#EF4444',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      animation: {
        'glow-pulse': 'glow-pulse 2s ease-in-out infinite',
        'border-dance': 'border-dance 3s linear infinite',
        'fade-in': 'fade-in 0.3s ease-out',
        'slide-up': 'slide-up 0.4s ease-out',
        'slide-right': 'slide-right 0.3s ease-out',
        'spin-slow': 'spin 3s linear infinite',
      },
      keyframes: {
        'glow-pulse': {
          '0%, 100%': { boxShadow: '0 0 20px oklch(0.62 0.24 320 / 0.3)' },
          '50%': { boxShadow: '0 0 40px oklch(0.62 0.24 320 / 0.6)' },
        },
        'border-dance': {
          '0%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
          '100%': { backgroundPosition: '0% 50%' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'slide-up': {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-right': {
          '0%': { transform: 'translateX(100%)' },
          '100%': { transform: 'translateX(0)' },
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
};
