import { useState, useEffect, useRef, useCallback } from 'react';

// Types for WebSocket messages
interface WebSocketMessage {
  status: 'success' | 'error';
  mode: 'snapshot' | 'live';
  source?: string;
  data?: any;
  error?: string;
  timestamp: string;
}

interface LiveMarketData {
  symbol: string;
  spot: number;
  calls: any[];
  puts: any[];
  analytics: any;
  intelligence: any;
  timestamp: string;
}

interface UseLiveMarketDataReturn {
  data: LiveMarketData | null;
  loading: boolean;
  error: string | null;
  mode: 'loading' | 'snapshot' | 'live' | 'error';
  websocket: WebSocket | null;
}

export function useLiveMarketDataNoRest(symbol: string, expiry: string): UseLiveMarketDataReturn {
  const [data, setData] = useState<LiveMarketData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<'loading' | 'snapshot' | 'live' | 'error'>('loading');
  const [websocket, setWebSocket] = useState<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef<number>(0);

  // WebSocket connection logic
  const connectWebSocket = useCallback(() => {
    try {
      console.log(`🔌 Connecting to WebSocket for ${symbol}...`);
      
      // Use environment variables for WebSocket URL
      const wsBaseUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
      const wsUrl = `${wsBaseUrl}/ws/live-options/${symbol}`;
      
      console.log("🔍 DEBUG: Connecting to WS URL:", wsUrl);
      console.log("🔍 DEBUG: Window location:", window.location.href);
      console.log("🔍 DEBUG: Protocol:", window.location.protocol);
      console.log("🔍 DEBUG: WS Base URL:", wsBaseUrl);
      
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log(`✅ WebSocket connected for ${symbol}`);
        setWebSocket(ws);
        setError(null);
        reconnectAttemptsRef.current = 0;
        
        // Clear any existing reconnect timeout
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };
      
      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log(`📨 WebSocket message for ${symbol}:`, message);
          console.log("🔍 DATA SOURCE:", message.source);
          
          if (message.status === 'success') {
            if (message.mode === 'snapshot') {
              console.log('📸 Received snapshot from WebSocket');
              setData(message.data);
              setMode('snapshot');
              setLoading(false);
            } else if (message.mode === 'live') {
              console.log('🔄 Received live update from WebSocket');
              setData(message.data);
              setMode('live');
              setLoading(false);
            }
          } else if (message.status === 'error') {
            console.error(`❌ WebSocket error for ${symbol}:`, message.error);
            setError(message.error || 'WebSocket error occurred');
            setMode('error');
            setLoading(false);
          }
        } catch (parseError) {
          console.error(`❌ Failed to parse WebSocket message:`, parseError);
          setError('Failed to parse WebSocket message');
          setMode('error');
          setLoading(false);
        }
      };
      
      ws.onclose = (event) => {
        console.log(`🔌 WebSocket closed for ${symbol}. Code: ${event.code}, Reason: ${event.reason}`);
        setWebSocket(null);
        
        // NO REST FALLBACK - JUST LOG THE ERROR
        if (event.code !== 1000 && reconnectAttemptsRef.current < 5) {
          console.log(`🔄 Attempting WebSocket reconnect ${reconnectAttemptsRef.current + 1}/5`);
          reconnectAttemptsRef.current++;
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connectWebSocket();
          }, 3000); // Wait 3 seconds before reconnecting
        } else {
          console.log(`🔌 WebSocket permanently closed for ${symbol}`);
          setError('WebSocket connection failed - NO REST FALLBACK');
          setMode('error');
          setLoading(false);
        }
      };
      
      ws.onerror = (event) => {
        console.error(`❌ WebSocket error for ${symbol}:`, event);
        setError('WebSocket connection error - NO REST FALLBACK');
        setMode('error');
        setLoading(false);
      };
      
    } catch (error) {
      console.error(`❌ Failed to create WebSocket for ${symbol}:`, error);
      setError('Failed to create WebSocket connection - NO REST FALLBACK');
      setMode('error');
      setLoading(false);
    }
  }, [symbol]);

  // Initialize WebSocket on mount
  useEffect(() => {
    console.log(`🚀 Initializing live market data for ${symbol} (NO REST FALLBACK)`);
    
    // Start WebSocket connection
    connectWebSocket();
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      
      if (websocket) {
        websocket.close();
      }
    };
  }, [symbol, connectWebSocket, mode]);

  return {
    data,
    loading,
    error,
    mode,
    websocket
  };
}
