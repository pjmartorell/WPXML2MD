module.exports = {
  content: ["./*.html"],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#06b6d4', // cyan-500
          hover: '#0891b2', // cyan-600
          light: '#22d3ee', // cyan-400
          dark: '#0e7490', // cyan-700
        },
        accent: {
          DEFAULT: '#2dd4bf', // teal-400
          hover: '#14b8a6', // teal-500
          light: '#5eead4', // teal-300
        },
        dark: {
          DEFAULT: '#020617', // slate-950
          lighter: '#0f172a', // slate-900
          darker: '#000000', // pure black
          mid: '#1e293b', // slate-800
        },
        text: {
          primary: '#f1f5f9', // slate-100 (On dark: 15.2:1 contrast ratio)
          secondary: '#e2e8f0', // slate-200 (On dark: 13.5:1 contrast ratio)
          muted: '#cbd5e1', // slate-300 (On dark: 11.5:1 contrast ratio)
          inverse: '#0f172a', // slate-900 (On light: 16:1 contrast ratio)
        }
      }
    }
  },
  darkMode: 'class'
}
