/**
 * Authentication utilities for managing persistent auth state
 */

export const AUTH_STORAGE_KEY = "strikeiq_authenticated";

export function setAuthenticated(persist: boolean = true) {
  if (persist) {
    localStorage.setItem(AUTH_STORAGE_KEY, "true");
    console.log("💾 Auth state persisted to localStorage");
  } else {
    localStorage.setItem(AUTH_STORAGE_KEY, "false");
    console.log("💾 Auth state updated in localStorage");
  }
}

export function clearAuthenticated() {
  localStorage.removeItem(AUTH_STORAGE_KEY);
  console.log("🗑️ Auth state cleared from localStorage");
}

export function isAuthenticatedPersisted(): boolean {
  return localStorage.getItem(AUTH_STORAGE_KEY) === "true";
}

export function forceReauth() {
  clearAuthenticated();
  // Force page reload to trigger re-authentication
  window.location.href = "/auth";
}
