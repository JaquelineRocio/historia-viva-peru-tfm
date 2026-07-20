/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  // Los colores de subtemas vienen de la taxonomía por API (labels_taxonomy),
  // no de clases Tailwind.
  theme: {
    extend: {},
  },
  plugins: [],
};
