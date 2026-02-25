/**
 * WebSocket Connection Manager Component
 * Ensures persistent WebSocket connection for market data
 */

import { useEffect, useRef } from 'react';
import { useWSStore } from '@/core/ws/wsStore';

interface WebSocketManagerProps {
  symbol: string;
  expiry: string;
}

const WebSocketManager = ({ symbol, expiry }: WebSocketManagerProps) => {
  const wsRef = useRef<WebSocket | null>(null);
  const symbolRef = useRef(symbol);
  const expiryRef = useRef(expiry);
  const { setWS, setConnected, setMarketData, setLiveData, setError } = useWSStore();

  // Update refs when props change (but don't reconnect)
  useEffect(() => {
    symbolRef.current = symbol;
    expiryRef.current = expiry;
  }, [symbol, expiry]);

  const connectWebSocket = async () => {
    // Prevent reconnect if already open
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('🔒 WS Manager: WebSocket already open, skipping connection');
      return;
    }

    try {
      console.log('🔒 WS Manager: Initializing WebSocket connection...');
      
      const initUrl = "http://127.0.0.1:8000/api/ws/init";
      console.log("🌐 REST CALL DETECTED:", initUrl);
      console.log("🌐 REST METHOD: GET");
      console.log("🌐 REST TIMESTAMP:", new Date().toISOString());

      const start = performance.now();

      // Call /api/ws/init first
      const initResponse = await fetch(initUrl, {
        method: "GET",
        credentials: "include"
      });

      const duration = performance.now() - start;
      console.log("🌐 REST STATUS:", initResponse.status);
      console.log("🌐 REST DURATION:", `${duration.toFixed(2)}ms`);

      if (!initResponse.ok) {
        throw new Error(`WebSocket init failed: ${initResponse.status}`);
      }

      console.log('🔒 WS Manager: Init successful, creating WebSocket...');

      // Create WebSocket connection with dynamic symbol/expiry from refs
      const ws = new WebSocket(`ws://127.0.0.1:8000/ws/live-options/${symbolRef.current}?expiry=${expiryRef.current}`);
      
      wsRef.current = ws;
      setWS(ws);

      ws.onopen = () => {
        console.log('🔒 WS Manager: Connected successfully');
        setConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          // IGNORE market status payload
          if (data.status === "market_data") {
            console.log("ℹ️ Ignoring market status WS payload");
            return;
          }

          // Accept ANY valid option chain payload
          if ("calls" in data && "puts" in data) {
            console.log("🔥 OPTION CHAIN RECEIVED:", data);

            // FORCE Zustand re-render
            setLiveData({
                ...data,
                _ts: Date.now()
            });

            setConnected(true);
          }

        } catch (e) {
          console.error("WS Parse Error", e);
        }
      };

      ws.onclose = (event) => {
        console.log(`🔒 WS Manager: Closed - Code: ${event.code}, Reason: ${event.reason}`);
        setConnected(false);
        setWS(null);
        wsRef.current = null;
      };

      ws.onerror = (error) => {
        console.error('🔒 WS Manager: Connection error', error);
        setError('WebSocket connection error');
      };

    } catch (error) {
      console.error('🔒 WS Manager: Failed to connect:', error);
      setError(error instanceof Error ? error.message : 'Failed to connect WebSocket');
    }
  };

  // Mount-only effect - no dependencies to prevent reconnection on prop changes
  useEffect(() => {
    connectWebSocket();
    
    // CRITICAL: No cleanup that closes WebSocket
    return () => {
      console.log("WS cleanup skipped to prevent reconnect loop");
    };
  }, []); // Empty dependency array - mount only

  // This component doesn't render anything - it just manages the connection
  return null;
};

export default WebSocketManager;
