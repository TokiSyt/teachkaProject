/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "../templates/**/*.html",
    "../../templates/**/*.html",
    "../../apps/**/*.html",
    "../../apps/**/*.py",
  ],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    fontFamily: {
      body: ["Poppins", "system-ui", "sans-serif"],
    },
    extend: {
      colors: {
        primary: {
          50: "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
          800: "#1e40af",
          900: "#1e3a8a",
        },
      },
    },
  },
  plugins: [require("daisyui").default ?? require("daisyui")],
  daisyui: {
    themes: [
      "light",
      "dark",
      "lemonade",
      "fantasy",
      "pastel",
    ],
    darkTheme: "dark",
    base: true,
    styled: true,
    utils: true,
  },
};
