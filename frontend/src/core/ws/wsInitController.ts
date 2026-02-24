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

    const response = await fetch('/api/ws/init', {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      // 500 most commonly means the backend already has an active session
      // (e.g. after a browser tab refresh the sessionStorage is cleared but
      // the backend still holds the connection). Treat this as "already up".
      if (response.status === 500 || response.status === 409) {
        console.warn(
          `🔒 WS Init: Backend returned ${response.status} — session likely already active, proceeding.`
        );
        markWSInitialized();
        return { status: 'connected', message: 'Session already active on backend' };
      }

      // For real client errors (401, 403, 400...) fail fast so the user knows
      throw new Error(`WS Init failed: ${response.status} ${response.statusText}`);
    }

    const data: WSInitResponse = await response.json();

    if (data.status === 'success' || data.status === 'connected') {
      console.log('🔒 WS Init: Successfully initialized WebSocket session');
      return data;
    } else {
      throw new Error(data.message || 'WS Init returned error status');
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
 * Clear the initialized flag so the next connect() attempt
 * goes through the full init flow (used by the recovery poller)
 */
export function clearWSInitialized(): void {
  sessionStorage.removeItem('ws_initialized');
  console.log('🔒 WS Init: Cleared — will re-initialize on next connect');
}
