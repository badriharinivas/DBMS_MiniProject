import type { Config } from "tailwindcss";
const config: Config = { content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"], theme: { extend: { colors: { ink: "#182621", forest: "#155c45", mint: "#e7f3ed", paper: "#f7f8f5", line: "#e6e9e4", muted: "#69756e", gold: "#bd8b38" }, boxShadow: { soft: "0 12px 35px rgba(20, 52, 39, .07)" }, fontFamily: { sans: ["Arial", "sans-serif"] } } }, plugins: [] };
export default config;
