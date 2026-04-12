import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        mc: {
          ink: 'oklch(0.96 0.005 60)',
          'ink-muted': 'oklch(0.55 0.008 60)',
          bg: 'oklch(0.07 0.008 60)',
          surface: 'oklch(0.11 0.008 60)',
          border: 'oklch(0.18 0.005 60)',
          accent: 'oklch(0.65 0.18 42)',
          red: 'oklch(0.58 0.20 22)',
          yellow: 'oklch(0.75 0.15 75)',
          green: 'oklch(0.65 0.14 145)',
        },
      },
      fontFamily: {
        sans: ['Geist', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Playfair Display', 'Georgia', 'serif'],
      },
    },
  },
  plugins: [],
};

export default config;
