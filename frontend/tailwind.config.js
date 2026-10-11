/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Legacy primary kept for backward compatibility
        primary: {
          50:  '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
        // New brand palette — Emerald green
        brand: {
          50:  '#ecfdf5',
          100: '#d1fae5',
          200: '#a7f3d0',
          300: '#6ee7b7',
          400: '#34d399',
          500: '#10b981',
          600: '#047857',   // Primary brand #047857
          700: '#065f46',
          800: '#064e3b',
          900: '#022c22',
        },
        // Lime accent
        lime: {
          50:  '#f7fee7',
          100: '#ecfccb',
          200: '#d9f99d',
          300: '#bef264',
          400: '#a3e635',   // Fresh lime #A3E635
          500: '#84cc16',
          600: '#65a30d',
          700: '#4d7c0f',
        },
        // Cream background
        cream: {
          50:  '#fffef7',
          100: '#fffbeb',   // Cream #FFFBEB
          200: '#fef3c7',
          300: '#fde68a',
        },
        // Orange accent
        accent: {
          50:  '#fff7ed',
          100: '#ffedd5',
          200: '#fed7aa',
          300: '#fdba74',
          400: '#fb923c',
          500: '#f97316',   // Orange accent #F97316
          600: '#ea580c',
          700: '#c2410c',
        },
        // Dark neutral
        neutral: {
          900: '#1f2937',   // Dark neutral #1F2937
          800: '#374151',
          700: '#4b5563',
          600: '#6b7280',
          500: '#9ca3af',
          400: '#d1d5db',
          300: '#e5e7eb',
          200: '#f3f4f6',
          100: '#f9fafb',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card:   '0 1px 3px 0 rgb(0 0 0 / 0.07), 0 1px 2px -1px rgb(0 0 0 / 0.05)',
        'card-md': '0 4px 6px -1px rgb(0 0 0 / 0.07), 0 2px 4px -2px rgb(0 0 0 / 0.04)',
        'brand':  '0 0 0 3px rgb(4 120 87 / 0.2)',
      },
      borderRadius: {
        'xl':  '0.75rem',
        '2xl': '1rem',
        '3xl': '1.25rem',
      },
    },
  },
  plugins: [],
}
