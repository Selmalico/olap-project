/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: { DEFAULT: '#1E3A5F', light: '#2E75B6' },
        accent: '#00B0F0'
      }
    }
  },
  plugins: [],
}
