/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          500: '#3C50E0',
          600: '#3142c5',
        }
      }
    },
  },
  plugins: [],
}
