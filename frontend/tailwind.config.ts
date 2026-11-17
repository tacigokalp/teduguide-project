import type { Config } from 'tailwindcss';

/**
 * Design tokens from the prototype (Project.md §6.2), with contrast fixes for WCAG 2.1 AA.
 * Contrast measured against bg / card / cardHi:
 *   text   #f0f2f5  17.6 / 15.9 / 14.5
 *   text2  #8e97ac   6.7 /  6.1 /  5.6
 *   text3  #808aa0   5.7 /  5.1 /  4.7   (prototype #4e5668 was 2.7; Project.md's #7c869b fails on cardHi at 4.44)
 *   red    #ef4444   5.2 /  4.7 /  4.3   -> use as text/icon colour on bg and card only
 *   redStrong #dc2626: background for buttons with white text (white on it = 4.8; white on #ef4444 = 3.8 fails)
 */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#080b12',
        bg2: '#0d1119',
        card: '#141820',
        cardHi: '#1a2030',
        text: '#f0f2f5',
        text2: '#8e97ac',
        text3: '#808aa0',
        red: '#ef4444',
        redStrong: '#dc2626',
        green: '#22c55e',
        blue: '#3b82f6',
        orange: '#f59e0b',
        purple: '#a78bfa',
        cyan: '#06b6d4',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      minHeight: { touch: '44px' }, // WCAG touch target
      minWidth: { touch: '44px' },
    },
  },
  plugins: [],
} satisfies Config;
