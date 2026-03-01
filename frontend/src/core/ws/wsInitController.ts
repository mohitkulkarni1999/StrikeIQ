/**
 * 🔒 WS CONNECTION LIFECYCLE - LOCKED MODULE
 *
 * Controls:
 * - OAuth Success → WS Init
 * - Single WS Handshake
 * - Live Market Feed Lifecycle
 *
 * DO NOT MODIFY WITHOUT ARCHITECTURAL CHANGE
 *
 * Modifying this may cause:
 * - /api/ws/init loop
 * - Backend flooding
 * - Reconnect storm
 * - Market feed disconnect
 */

interface WSInitResponse {
  status: 'success' | 'error' | 'connected';
  message?: string;
  session_id?: string;
}

/**
 * Initialize WebSocket connection after successful OAuth
 * This function should only be called once per OAuth success
 */
export async function initWebSocketOnce(): Promise<WSInitResponse> {
  try {
    console.log('🔒 WS Init: Starting single WebSocket initialization');

    const response = await fetch('/api/ws/init');

    if (!response.ok) {
      console.warn('🔒 WS Init HTTP error', response.status);
      return null;
    }

    const data = await response.json();

    if (!data || typeof data !== "object") {
      console.warn('🔒 WS Init invalid response', data);
      return null;
    }

    if (data.status === 'success' || data.status === 'connected') {
      console.log('🔒 WS Init: Successfully initialized WebSocket session');
      return data;
    } else {
      console.warn('🔒 WS Init returned non-success', data);
      return null;
    }
  } catch (error) {
    console.error('🔒 WS Init: Initialization failed', error);
    return {
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error during WS init'
    };
  }
}

/**
 * Check if WebSocket is already initialized
 * Prevents multiple initialization attempts
 */
export function isWSInitialized(): boolean {
  // Check if WebSocket session exists in cookies/storage
  return document.cookie.includes('ws_session=') ||
    sessionStorage.getItem('ws_initialized') === 'true';
}

/**
 * Mark WebSocket as initialized
 * Prevents re-initialization
 */
export function markWSInitialized(): void {
  sessionStorage.setItem('ws_initialized', 'true');
  console.log('🔒 WS Init: Marked as initialized');
}

/**
 * Clear initialized flag so next connect() attempt
 * goes through the full init flow (used by recovery poller)
 */
export function clearWSInitialized(): void {
  sessionStorage.removeItem('ws_initialized');
  console.log('🔒 WS Init: Cleared — will re-initialize on next connect');
}
