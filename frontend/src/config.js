// Chameleon API & WebSocket Configuration Helper
export const API_BASE = (import.meta.env.VITE_BACKEND_API_URL || 'http://localhost:8000').replace(/\/$/, '')

export const WS_BASE = API_BASE.replace(/^http/, 'ws')
