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
    isConnected,
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
  // Keep a stable ref to options so connect() never needs to recreate
  const optionsRef = useRef(options);
  optionsRef.current = options;

  // Calculate next Thursday expiry if not provided
  const getNextThursdayExpiry = useCallback(() => {
    const today = new Date();
    const daysUntilThursday = (4 - today.getDay() + 7) % 7 || 7;
    const thursday = new Date(today);
    thursday.setDate(today.getDate() + daysUntilThursday);
    return thursday.toISOString().split('T')[0];
  }, []);

  // Stable connect — reads state directly from store, not from reactive deps
  const connect = useCallback(async () => {
    if (!mountedRef.current) return;

    // Read current state directly from store to avoid stale closures
    const { isConnected: connected, isInitializing: initializing, reconnectAttempts, maxReconnectAttempts } = useWSStore.getState();

    // Prevent multiple connections
    if (connected || initializing) {
      console.log('🔒 WS: Already connected or initializing, skipping');
      return;
    }

    // Check if already initialized
    if (!isWSInitialized()) {
      console.log('🔒 WS: Not initialized, calling init first');
      setInitializing(true);

      const initResult = await initWebSocketOnce();
      if (initResult.status !== 'success' && initResult.status !== 'connected') {
        setError(initResult.message || 'WS initialization failed');
        setInitializing(false);
        return;
      }

      markWSInitialized();
      setInitializing(false);
    }

    // Build WebSocket URL dynamically
    const { symbol, expiry } = optionsRef.current;
    const finalExpiry = expiry || getNextThursdayExpiry();
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.hostname;
    const wsUrl = `${wsProtocol}//${wsHost}:8000/ws/live-options/${symbol}?expiry=${encodeURIComponent(finalExpiry)}`;

    console.log(`🔒 WS: Connecting to ${wsUrl}`);
    const websocket = new WebSocket(wsUrl);
    setWS(websocket);

    websocket.onopen = () => {
      if (!mountedRef.current) return;
      console.log('🔒 WS: Connected successfully');
      setConnected(true);
      setError(null);
      resetReconnectAttempts();
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
      optionsRef.current.onDisconnect?.();

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
          if (mountedRef.current) connect();
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
      optionsRef.current.onError?.('WebSocket connection error');
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [getNextThursdayExpiry, setWS, setConnected, setError, resetReconnectAttempts, setInitializing, incrementReconnectAttempts, setMarketData]); // stable — reads live store state via getState()

  // Run ONCE on mount only — no [connect, ws] dependency that causes re-runs
  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      // DO NOT close WebSocket here - keep connection alive
      // useWSStore.getState().ws?.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // intentionally empty — connect once on mount

  // Manual disconnect function
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    useWSStore.getState().ws?.close(1000, 'Manual disconnect');
  }, []);

  return {
    ws,
    isConnected,
    isInitializing,
    disconnect,
    reconnect: connect
  };
}
