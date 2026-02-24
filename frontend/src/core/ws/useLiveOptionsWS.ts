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
    setError,
    incrementReconnectAttempts,
    resetReconnectAttempts,
    reconnectAttempts,
    maxReconnectAttempts
  } = useWSStore();

  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef<boolean>(true);

  // Calculate next Thursday expiry if not provided
  const getNextThursdayExpiry = useCallback(() => {
    const today = new Date();
    const thursday = new Date(today);
    const daysUntilThursday = (4 - today.getDay() + 7) % 7 || 7;
    thursday.setDate(today.getDate() + daysUntilThursday);
    return thursday.toISOString().split('T')[0];
  }, []);

  // Build WebSocket URL
  const buildWSUrl = useCallback((symbol: string, expiry: string) => {
    const finalExpiry = expiry || getNextThursdayExpiry();
    return `ws://localhost:8000/ws/live-options/${symbol}?expiry=${encodeURIComponent(finalExpiry)}`;
  }, [getNextThursdayExpiry]);

  // Connect to WebSocket
  const connect = useCallback(async () => {
    if (!mountedRef.current) return;
    
    // Prevent multiple connections
    if (isConnected || isInitializing) {
      console.log('🔒 WS: Already connected or initializing, skipping');
      return;
    }

    // Check if already initialized
    if (!isWSInitialized()) {
      console.log('🔒 WS: Not initialized, calling init first');
      setInitializing(true);
      
      const initResult = await initWebSocketOnce();
      if (initResult.status !== 'success') {
        setError(initResult.message || 'WS initialization failed');
        setInitializing(false);
        return;
      }
      
      markWSInitialized();
      setInitializing(false);
    }

    // Create WebSocket connection
    const wsUrl = buildWSUrl(options.symbol, options.expiry);
    console.log(`🔒 WS: Connecting to ${wsUrl}`);
    
    const websocket = new WebSocket(wsUrl);
    setWS(websocket);

    websocket.onopen = () => {
      if (!mountedRef.current) return;
      
      console.log('🔒 WS: Connected successfully');
      setConnected(true);
      setError(null);
      resetReconnectAttempts();
      
      if (options.onConnect) {
        options.onConnect();
      }
    };

    websocket.onmessage = (event) => {
      if (!mountedRef.current) return;
      
      try {
        const data = JSON.parse(event.data);
        setLastMessage(data);
        
        if (options.onMessage) {
          options.onMessage(data);
        }
      } catch (error) {
        console.error('🔒 WS: Failed to parse message', error);
      }
    };

    websocket.onclose = (event) => {
      if (!mountedRef.current) return;
      
      console.log(`🔒 WS: Closed - Code: ${event.code}, Reason: ${event.reason}`);
      setConnected(false);
      setWS(null);
      
      if (options.onDisconnect) {
        options.onDisconnect();
      }

      // Attempt reconnection if not manual close and under max attempts
      if (event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
        incrementReconnectAttempts();
        
        const delay = Math.min(10000, 1000 * 2 ** reconnectAttempts);
        console.log(`🔒 WS: Reconnecting in ${delay}ms (attempt ${reconnectAttempts + 1})`);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          if (mountedRef.current) {
            connect();
          }
        }, delay);
      } else if (reconnectAttempts >= maxReconnectAttempts) {
        setError('Max reconnection attempts reached. Please refresh the page.');
      }
    };

    websocket.onerror = (error) => {
      if (!mountedRef.current) return;
      
      console.error('🔒 WS: Connection error', error);
      setError('WebSocket connection error');
      
      if (options.onError) {
        options.onError('WebSocket connection error');
      }
    };
  }, [options, isConnected, isInitializing, buildWSUrl, isWSInitialized, setWS, setConnected, setInitializing, setLastMessage, setError, resetReconnectAttempts, incrementReconnectAttempts, reconnectAttempts, maxReconnectAttempts]);

  // Initialize connection on mount
  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      
      if (ws) {
        ws.close();
      }
    };
  }, [connect, ws]);

  // Manual disconnect function
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (ws) {
      ws.close(1000, 'Manual disconnect');
    }
  }, [ws]);

  return {
    ws,
    isConnected,
    isInitializing,
    disconnect,
    reconnect: connect
  };
}
