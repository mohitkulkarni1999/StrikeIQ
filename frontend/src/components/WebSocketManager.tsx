import { useEffect, useRef, useState } from 'react';
import { useWSStore } from '@/core/ws/wsStore';
import axios from 'axios';

interface WebSocketManagerProps {
  symbol: string;
  expiry: string;
}

const WebSocketManager = ({ symbol, expiry }: WebSocketManagerProps) => {
  const wsRef = useRef<WebSocket | null>(null);
  const symbolRef = useRef(symbol);
  const expiryRef = useRef(expiry);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 3000;
  
  let retryCount = 0;

  function retryInitWithBackoff() {
    if (window.location.pathname === "/auth") {
      return;
    }
    
    const delay = Math.min(3000 * (retryCount + 1), 15000);
    setTimeout(() => {
      retryCount++;
      initLiveFeed(symbolRef.current, expiryRef.current);
    }, delay);
  }
  
  const [isInitializing, setIsInitializing] = useState(false);
  const [initError, setInitError] = useState<string | null>(null);
  
  const { setWS, setConnected, setError } = useWSStore();

  useEffect(() => {
    symbolRef.current = symbol;
    expiryRef.current = expiry;
  }, [symbol, expiry]);

  const initLiveFeed = async (symbol: string, expiry: string): Promise<boolean> => {
    setIsInitializing(true);
    setInitError(null);
    
    if (window.location.pathname === "/auth") {
      console.warn("Skipping WS init on auth page");
      setIsInitializing(false);
      return false;
    }
    
    // Guard against multiple initializations
    if ((window as any).__STRIKEIQ_LIVE_WS__ && 
        (window as any).__STRIKEIQ_LIVE_WS__.readyState === WebSocket.OPEN) {
      console.warn("Live WS already exists and is open");
      setIsInitializing(false);
      return true;
    }
    
    // Guard against concurrent initialization
    if ((window as any).__STRIKEIQ_WS_INITIALIZING__) {
      console.warn("WS initialization already in progress");
      return false;
    }
    
    (window as any).__STRIKEIQ_WS_INITIALIZING__ = true;
    console.log('Initializing WebSocket feed...');
    
    try {
      await axios.get("/api/ws/init");
    } catch (error: any) {
      // TOKEN EXPIRED → WS AUTH FAILED
      if (error?.response?.status === 401 ||
          error?.response?.status === 403) {
        setIsInitializing(false);
        delete (window as any).__STRIKEIQ_WS_INITIALIZING__;
        return false;
      }

      // For other errors, fall through to general error handling
    }
    
    try {
      // Only after successful init, create WebSocket connection
      if (
        (window as any).__STRIKEIQ_LIVE_WS__ &&
        (window as any).__STRIKEIQ_LIVE_WS__.readyState === WebSocket.OPEN
      ) {
        console.warn("Live WS already exists and is open")
        delete (window as any).__STRIKEIQ_WS_INITIALIZING__;
        setIsInitializing(false);
        return (window as any).__STRIKEIQ_LIVE_WS__;
      }
      
      // Clean up any existing closed WebSocket
      if ((window as any).__STRIKEIQ_LIVE_WS__) {
        (window as any).__STRIKEIQ_LIVE_WS__.close();
        (window as any).__STRIKEIQ_LIVE_WS__ = null;
      }
      
      // Use global store instead of creating WebSocket
      const { connect } = useWSStore();
      const ws = connect(symbol, expiry);
      
      (window as any).__STRIKEIQ_LIVE_WS__ = ws;
      
      wsRef.current = ws;
      setWS(ws);

      ws.onopen = () => {
        console.log('WebSocket connected successfully');
        setConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
        setIsInitializing(false);
        delete (window as any).__STRIKEIQ_WS_INITIALIZING__;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.status === "market_data") return;

          if ("calls" in data && "puts" in data) {
            const unifiedPayload = {
              ...data,
              _ts: Date.now()
            };

            // 🔥 Synchronous STORE WRITE (NO REACT TIMING DELAY)
            useWSStore.setState({
              liveData: unifiedPayload,
              wsLiveData: unifiedPayload,
              optionChainSnapshot: unifiedPayload
            });

            setConnected(true);
          }
        } catch (err) {
          setError('Failed to parse WebSocket message');
        }
      };

      ws.onclose = (event) => {
        setConnected(false);
        setWS(null);
        wsRef.current = null;
        
        // Clean up global reference
        if ((window as any).__STRIKEIQ_LIVE_WS__ === ws) {
          delete (window as any).__STRIKEIQ_LIVE_WS__;
        }
        delete (window as any).__STRIKEIQ_WS_INITIALIZING__;

        // Attempt reconnection if not manually closed and under max attempts
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;

          reconnectTimeoutRef.current = setTimeout(() => {
            // Check if already reconnected before attempting
            if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
              connectWebSocket();
            }
          }, reconnectDelay);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          setInitError('Max reconnection attempts reached');
          setIsInitializing(false);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('WebSocket connection error');
        setIsInitializing(false);
        delete (window as any).__STRIKEIQ_WS_INITIALIZING__;
      };

      return true;

    } catch (error: any) {
      console.error('Failed to initialize WebSocket feed:', error);
      setInitError(error.message);
      setError(error.message);
      setIsInitializing(false);
      delete (window as any).__STRIKEIQ_WS_INITIALIZING__;
      
      // Retry logic for init failure
      if (reconnectAttemptsRef.current < maxReconnectAttempts) {
        reconnectAttemptsRef.current++;
        
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket();
        }, reconnectDelay);
      } else {
        setInitError('Failed to initialize WebSocket after multiple attempts');
        setIsInitializing(false);
      }
      
      return false;
    }
  };

  const connectWebSocket = async () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return;
    }

    if (isInitializing) {
      return;
    }

    await initLiveFeed(symbolRef.current, expiryRef.current);
  };

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect');
      wsRef.current = null;
    }
    
    // Clean up global references
    delete (window as any).__STRIKEIQ_LIVE_WS__;
    delete (window as any).__STRIKEIQ_WS_INITIALIZING__;
    
    setWS(null);
    setConnected(false);
    reconnectAttemptsRef.current = 0;
    setIsInitializing(false);
    setInitError(null);
  };

  useEffect(() => {
    connectWebSocket();
    
    return () => {
      // FIX 6: Ensure WebSocket connection is properly closed
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      disconnect();
    };
  }, []);

  // Debug logging for state changes (removed console.log for production)
  useEffect(() => {
    // Debug state changes can be logged here in development
  }, [isInitializing, initError]);

  return null;
};

export default WebSocketManager;