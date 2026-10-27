// Central backend API base URL.
// Override at build time with a VITE_API_URL environment variable (e.g. in production).
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
