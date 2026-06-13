/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1f2933",
        rosewood: "#9f3a4a",
        mint: "#2f7d6d",
        paper: "#f8f6f1",
      },
    },
  },
  plugins: [],
};
