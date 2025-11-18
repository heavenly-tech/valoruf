/** @type {import('tailwindcss').Config} */
module.exports = {
    // Tell Tailwind to scan your index.html and app.js for classes
    content: [
      "./static/index.html", 
      "./static/app.js"
    ],
    theme: {
      extend: {
        fontFamily: {
          sans: ['Inter', 'sans-serif'],
        },
        colors: {
          'primary-blue': '#1e40af', 
          'text-dark': '#1f2937',
        }
      }
    },
    plugins: [],
  }
