/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#e6f7ff',
          100: '#b3e8ff',
          500: '#0099ff',
          600: '#007acc',
          900: '#003366',
        },
        dark: {
          900: '#0B0F17',
          800: '#111827',
          700: '#1F2937',
          600: '#374151'
        }
      }
    },
  },
  plugins: [],
}
