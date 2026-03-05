const isDevelopment = process.env.NODE_ENV === 'development'
const UI_DEBUG = isDevelopment ? false : false
const WS_DEBUG = isDevelopment ? false : false
const API_DEBUG = isDevelopment ? false : false

export function uiLog(message: string, data?: any) {
  if (!UI_DEBUG) return
  console.debug("[UI]", message, data || "")
}

export function wsLog(message: string, data?: any) {
  if (!WS_DEBUG) return
  console.debug("[WS]", message, data || "")
}

export function apiLog(message: string, data?: any) {
  if (!API_DEBUG) return
  console.debug("[API]", message, data || "")
}

export function wsError(message: string, data?: any) {
  console.error("[WS ERROR]", message, data || "")
}

export function apiError(message: string, data?: any) {
  console.error("[API ERROR]", message, data || "")
}

export function uiError(message: string, data?: any) {
  console.error("[UI ERROR]", message, data || "")
}

// Production-safe critical logs (always shown)
export function wsCritical(message: string, data?: any) {
  console.log("[WS]", message, data || "")
}

export function apiCritical(message: string, data?: any) {
  console.log("[API]", message, data || "")
}

export function uiCritical(message: string, data?: any) {
  console.log("[UI]", message, data || "")
}
