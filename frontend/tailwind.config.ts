import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bone: { DEFAULT: '#F4EFE6', deep: '#EAE2D4' },
        paper: '#FBF8F2',
        ink: { DEFAULT: '#1C1B17', soft: '#3A382F' },
        mute: { DEFAULT: '#8B8676', lite: '#B8B2A1' },
        line: '#D8D0BE',
        olive: { DEFAULT: '#3D4A2A', deep: '#2A3420' },
        clay: '#B85C3A',
        sand: '#D9C9A8',
        sky: '#A8B5B0',
        card: { DEFAULT: '#FFFFFF', soft: '#FEFCF6' },
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        serif: ['var(--font-instrument-serif)', 'Fraunces', 'Georgia', 'serif'],
        mono: ['var(--font-jetbrains-mono)', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        low: '0 1px 0 rgba(28,27,23,0.04), 0 1px 2px rgba(28,27,23,0.06)',
        med: '0 2px 0 rgba(28,27,23,0.04), 0 12px 24px -12px rgba(28,27,23,0.15)',
        hi: '0 2px 0 rgba(28,27,23,0.05), 0 24px 48px -18px rgba(28,27,23,0.22)',
      },
      screens: { md: '768px', lg: '1024px', xl: '1440px' },
    },
  },
  plugins: [],
};

export default config;
