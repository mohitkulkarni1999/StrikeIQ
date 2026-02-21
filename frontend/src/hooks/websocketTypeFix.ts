/**
 * WebSocket Type Safety Fix
 * Resolves TypeScript error: Property 'readyState' does not exist on type 'EventTarget'
 */

// Type guard to safely check if event.target is a WebSocket
function isWebSocket(target: any): target is WebSocket {
    return target && typeof target === 'object' && 'readyState' in target && 'CLOSED' in target;
}

// Alternative type guard using duck typing
function isWebSocketEvent(event: Event): event is Event & { target: WebSocket } {
    return 'target' in event && 
           event.target !== null && 
           typeof event.target === 'object' && 
           'readyState' in event.target;
}

// Safe WebSocket extraction with proper typing
function getWebSocketFromEvent(event: Event): WebSocket | null {
    if (isWebSocketEvent(event)) {
        return event.target;
    }
    return null;
}

// Export safe type guards and helpers
export { isWebSocket, isWebSocketEvent, getWebSocketFromEvent };

// Example usage for fixing the error:
/*
// ❌ BEFORE (TypeScript error):
ws.onerror = (error) => {
    if (event.target && event.target.readyState === WebSocket.CLOSED) {
        console.log('WebSocket connection was rejected');
    }
};

// ✅ AFTER (Type-safe):
import { isWebSocket } from './websocketTypeFix';

ws.onerror = (error) => {
    if (isWebSocket(error.target) && event.target.readyState === WebSocket.CLOSED) {
        console.log('WebSocket connection was rejected - likely auth error');
    }
};

// ✅ ALTERNATIVE (Using helper):
import { getWebSocketSafely } from './websocketTypeFix';

ws.onerror = (error) => {
    const ws = getWebSocketSafely(error);
    if (ws && ws.readyState === WebSocket.CLOSED) {
        console.log('WebSocket connection was rejected - likely auth error');
    }
};
*/
