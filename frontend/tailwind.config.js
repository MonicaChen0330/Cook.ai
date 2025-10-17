/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#4A90E2',
        'primary-hover': '#357ABD',
        'primary-dark': '#4343e6',
        'text-default': '#212529',
        'text-light': '#495057',
        'text-muted': '#6C757D',
        'background-default': '#F8F9FA',
        'card-background': '#FFFFFF',
        'border-default': '#DEE2E6',
      },
      backgroundImage: {
        'primary-gradient': 'linear-gradient(90deg, #4343e6 0%, #81C7F5 100%)',
      },
      boxShadow: {
        'default': '0 4px 6px rgba(0,0,0,0.05)',
        'lg': '0 8px 15px rgba(0,0,0,0.1)', // From portal-card:hover
      },
      borderRadius: {
        'default': '8px',
      },
    },
  },
  plugins: [],
}
