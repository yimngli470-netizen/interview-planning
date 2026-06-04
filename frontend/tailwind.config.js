/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  // Domain colors are applied via dynamic class names, so safelist them.
  safelist: [
    { pattern: /(bg|text|border)-(blue|violet|emerald|amber|rose|indigo|slate)-(100|200|500|600|700)/ },
  ],
  theme: { extend: {} },
  plugins: [],
};
