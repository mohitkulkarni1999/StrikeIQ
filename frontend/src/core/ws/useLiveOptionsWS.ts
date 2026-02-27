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

import { useEffect, useRef, useCallback } from 'react';
import { useWSStore } from './wsStore';
import { initWebSocketOnce, isWSInitialized, markWSInitialized } from './wsInitController';
import { getValidExpiries } from '@/lib/axios';

interface LiveOptionsWSOptions {
  symbol: string;
  expiry: string;
  onMessage?: (data: any) => void;
  onError?: (error: string) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

/**
 * WebSocket hook for live options data
 * Enforces single connection pattern and prevents reconnection storms
 */
export function useLiveOptionsWS(options: LiveOptionsWSOptions) {
  const {
    ws,
    connected,
    isInitializing,
    setWS,
    setConnected,
    setInitializing,
    setLastMessage,
    setMarketData,
    setError,
    incrementReconnectAttempts,
    resetReconnectAttempts,
  } = useWSStore();

  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef<boolean>(true);
  const initializedRef = useRef<boolean>(false);
  // Keep a stable ref to options so connect() never needs to recreate
  const optionsRef = useRef(options);
  optionsRef.current = options;

  // Get valid expiry from backend registry
  const getValidExpiryFromBackend = useCallback(async (symbol: string): Promise<string> => {
    const expiries = await getValidExpiries(symbol);
    return expiries.length > 0 ? expiries[0] : '';
  }, []);

  // Stable connect — reads state directly from store, not from reactive deps
  const connect = useCallback(async () => {
    if (!mountedRef.current) return;

    // Read current state directly from store to avoid stale closures
    const { connected: isWsConnected, isInitializing, reconnectAttempts, maxReconnectAttempts } = useWSStore.getState();

    // Prevent multiple connections
    if (isWsConnected || isInitializing) {
      console.log('🔒 WS: Already connected or initializing, skipping');
      return;
    }

    // Check if already initialized
    if (!isWSInitialized()) {
      console.log('🔒 WS: Not initialized, calling init first');
      setInitializing(true);

      const initResult = await initWebSocketOnce();

      if (!initResult) {
        console.warn("WS init returned null");
        setError("WS initialization failed");
        setInitializing(false);
        return;
      }

      if (initResult.status !== 'success' && initResult.status !== 'connected') {
        setError(initResult.message || 'WS initialization failed');
        setInitializing(false);
        return;
      }

      markWSInitialized();
      setInitializing(false);
    } else {
      console.log('🔒 WS: Already initialized, skipping init');
    }

    // Build WebSocket URL dynamically
    const { symbol, expiry } = optionsRef.current;
    let finalExpiry = expiry;
    
    // ALWAYS fetch valid expiry from backend registry
    try {
      const expiries = await getValidExpiries(symbol);
      
      if (!expiries || expiries.length === 0) {
        throw new Error("No valid expiries available");
      }
      
      // PATCH 4 - Use first valid expiry
      const expiry = expiries[0];
      finalExpiry = expiry;
      console.log(`🔒 Using valid expiry from backend: ${finalExpiry}`);
      
    } catch (error) {
      console.error('Failed to get valid expiry:', error);
      setError('Failed to get valid expiry');
      return;
    }
    
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.hostname;
    const wsUrl = `${wsProtocol}//${wsHost}:8000/ws/live-options/${symbol}?expiry=${encodeURIComponent(finalExpiry)}`;

    console.log(`🔒 WS: Connecting to ${wsUrl}`);
    
    if (window.location.pathname === "/auth") {
      return;
    }
    
    // PATCH 5 — PREVENT FRONTEND RECONNECT STORM
    const currentState = useWSStore.getState();
    if (currentState.ws && currentState.ws.readyState === WebSocket.OPEN) {
      console.log("🔒 WS: Already connected with open socket")
      return
    }
    
    // PATCH 3 — ADD CONNECTION GUARD
    if ((window as any).STRIKEIQ_WS_CONNECTED) {
      console.log("🔒 WS: Connection guard - already marked as connected")
      return
    }
    
    (window as any).STRIKEIQ_WS_CONNECTED = true
    
    // Use global store instead of creating WebSocket
    const websocket = useWSStore().connect(symbol, expiry);
    setWS(websocket);

    websocket.onopen = () => {
      if (!mountedRef.current) return;
      console.log('🔒 WS: Connected successfully');
      setConnected(true);
      setError(null);
      resetReconnectAttempts();
      
      // Set connection guard
      (window as any).STRIKEIQ_WS_CONNECTED = true;
      
      optionsRef.current.onConnect?.();
    };

    websocket.onmessage = (event) => {
      if (!mountedRef.current) return;
      try {
        const data = JSON.parse(event.data);
        setLastMessage(data);
        
        // Store market_data in Zustand store
        if (data.status === 'market_data' && data.data) {
          setMarketData(data.data);
        }
        
        optionsRef.current.onMessage?.(data);
      } catch (error) {
        console.error('🔒 WS: Failed to parse message', error);
      }
    };

    websocket.onclose = (event) => {
      if (!mountedRef.current) return;
      console.log(`🔒 WS: Closed - Code: ${event.code}, Reason: ${event.reason}`);
      setConnected(false);
      setWS(null);
      
      // Clear connection guard
      delete (window as any).STRIKEIQ_WS_CONNECTED;
      
      optionsRef.current.onDisconnect?.();

      // TOKEN EXPIRED
      if (event.code === 1006 || event.code === 1008) {
        if (window.location.pathname !== "/auth") {
          window.location.href = "/auth";
        }
        return;
      }

      // Read fresh state for reconnect logic
      const { reconnectAttempts: attempts, maxReconnectAttempts: maxAttempts } = useWSStore.getState();

      // Code 1011 = Server Internal Error
      // This usually means "market closed / backend has no data to serve right now".
      // Use a much longer backoff (10s, 20s, 40s... max 60s) and cap at 3 retries
      // to avoid flooding the backend during off-market hours.
      const isServerError = event.code === 1011;
      const maxRetries = isServerError ? 3 : maxAttempts;
      const baseDelay = isServerError ? 10_000 : 1_000;

      if (event.code !== 1000 && attempts < maxRetries) {
        incrementReconnectAttempts();
        const delay = Math.min(60_000, baseDelay * 2 ** attempts);
        console.log(`🔒 WS: Reconnecting in ${delay}ms (attempt ${attempts + 1}${isServerError ? ', server-error backoff' : ''})`);
        reconnectTimeoutRef.current = setTimeout(() => {
          if (mountedRef.current) {
            // Check if already reconnected before attempting
            const currentState = useWSStore.getState();
            if (!currentState.ws || currentState.ws.readyState !== WebSocket.OPEN) {
              connect();
            } else {
              console.log('🔒 WS: Already reconnected, skipping retry');
            }
          }
        }, delay);
      } else if (attempts >= maxRetries) {
        console.warn(`🔒 WS: Max reconnection attempts (${maxRetries}) reached. Giving up.`);
        setError(
          isServerError
            ? 'Market data unavailable — backend may be closed or market is not open.'
            : 'Max reconnection attempts reached. Please refresh the page.'
        );
      }
    };

    websocket.onerror = (error) => {
      if (!mountedRef.current) return;
      console.error('🔒 WS: Connection error', error);
      setError('WebSocket connection error');
      
      // Clear connection guard on error
      delete (window as any).STRIKEIQ_WS_CONNECTED;
      
      optionsRef.current.onError?.('WebSocket connection error');
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [getValidExpiryFromBackend, setWS, setConnected, setError, resetReconnectAttempts, setInitializing, incrementReconnectAttempts, setMarketData]); // stable — reads live store state via getState()

  // Run ONCE on mount only — no [connect, ws] dependency that causes re-runs
  useEffect(() => {
    if (initializedRef.current) {
      console.log('🔒 WS: Already initialized, skipping StrictMode double mount');
      return
    }

    if ((window as any).STRIKEIQ_WS_CONNECTED) {
      console.log('🔒 WS: Already marked as connected on mount, skipping init');
      initializedRef.current = true;
      return
    }

    initializedRef.current = true;
    mountedRef.current = true;
    connect();
    
    return () => {
      mountedRef.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      // Clear connection guard on unmount
      delete (window as any).STRIKEIQ_WS_CONNECTED;
    };
  }, []); // intentionally empty — connect once on mount

  // Manual disconnect function
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    const currentState = useWSStore.getState();
    if (currentState.ws) {
      currentState.ws.close(1000, 'Manual disconnect');
    }
    
    // Clear connection guard
    delete (window as any).STRIKEIQ_WS_CONNECTED;
  }, []);

  return {
    ws,
    connected,
    isInitializing,
    disconnect,
    reconnect: connect
  };
}
