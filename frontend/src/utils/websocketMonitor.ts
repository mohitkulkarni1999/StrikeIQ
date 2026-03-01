/**
 * Global WebSocket Connection Monitor
 * Use this for debugging to verify only one WebSocket connection exists
 */

export function getGlobalWebSocketCount(): number {
  const globalWS = (window as any).__STRIKEIQ_GLOBAL_WS__;
  return globalWS ? 1 : 0;
}

export function getGlobalWebSocket(): WebSocket | null {
  return (window as any).__STRIKEIQ_GLOBAL_WS__ || null;
}

export function isGlobalWebSocketConnected(): boolean {
  const ws = getGlobalWebSocket();
  return ws ? ws.readyState === WebSocket.OPEN : false;
}

export function debugWebSocketConnections() {
  console.log('🔍 WebSocket Debug Info:');
  console.log('- Global WS Count:', getGlobalWebSocketCount());
  console.log('- Global WS Connected:', isGlobalWebSocketConnected());
  console.log('- Global WS State:', getGlobalWebSocket()?.readyState);
  
  // Check for any other WebSocket instances
  const originalWebSocket = (window as any).WebSocket;
  if (originalWebSocket) {
    console.log('- Original WebSocket constructor exists');
  }
}

// Auto-debug in development
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  setInterval(debugWebSocketConnections, 5000);
}
