import { useState, useEffect, useRef, useCallback } from 'react';
import api from '../src/lib/api';

// Types for WebSocket messages
interface WebSocketMessage {
  status: 'success' | 'error' | 'auth_required' | 'connected' | 'heartbeat';
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
  probability?: any;
  timestamp: string;
}

interface UseLiveMarketDataReturn {
  data: LiveMarketData | null;
  loading: boolean;
  error: string | null;
  mode: 'loading' | 'snapshot' | 'live' | 'error';
  websocket: WebSocket | null;
}

export function useLiveMarketData(symbol: string, expiry: string): UseLiveMarketDataReturn {
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
          
          // Handle authentication required
          if (message.status === 'auth_required') {
            console.warn('🔐 Authentication required - redirecting to auth screen');
            
            // Close WebSocket
            ws.close();
            
            // Dispatch auth expired event for global handling
            window.dispatchEvent(new Event('auth-expired'))
            return
          }
          
          // Handle connection success - don't update state, just log
          if (message.status === 'connected') {
            console.log('✅ WebSocket connection established');
            return; // Don't update state, wait for actual data
          }
          
          // Handle heartbeat - don't update state
          if (message.status === 'heartbeat') {
            console.log('💓 WebSocket heartbeat received');
            return; // Don't update state for heartbeat
          }
          
          // Handle success messages with actual data
          if (message.status === 'success') {
            if (message.mode === 'snapshot') {
              console.log('📸 Received snapshot from WebSocket');
              console.log("📡 WS UPDATE RECEIVED - SNAPSHOT");
              setData(message.data);
              setMode('snapshot');
              setLoading(false);
            } else if (message.mode === 'live') {
              console.log('🔄 Received live update from WebSocket');
              console.log("📡 WS UPDATE RECEIVED - LIVE");
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
        
        // Attempt reconnection if not a normal close
        if (event.code !== 1000 && reconnectAttemptsRef.current < 5) {
          console.log(`🔄 Attempting reconnection ${reconnectAttemptsRef.current + 1}/5...`);
          reconnectAttemptsRef.current++;
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connectWebSocket();
          }, 3000); // Wait 3 seconds before reconnecting
        } else {
          console.log(`🔌 WebSocket permanently closed for ${symbol}`);
          setError('WebSocket connection failed');
          setMode('error');
          setLoading(false);
        }
      };
      
      ws.onerror = (event) => {
        console.error(`❌ WebSocket error for ${symbol}:`, event);
        
        // Check if this is an authentication error (403)
        // The WebSocket error event doesn't give us status code, but we can check
        // if the connection was rejected immediately (typical for auth errors)
        if (event.target && event.target.readyState === WebSocket.CLOSED) {
          console.log('🔐 WebSocket connection was rejected - likely auth error');
          
          // Dispatch auth expired event to trigger auth flow
          window.dispatchEvent(new Event('auth-expired'));
          
          setError('Authentication required');
          setMode('error');
          setLoading(false);
          return;
        }
        
        setError('WebSocket connection error');
        setMode('error');
        setLoading(false);
      };
      
    } catch (error) {
      console.error(`❌ Failed to create WebSocket for ${symbol}:`, error);
      
      // Check if this is an authentication error
      if (error.message && error.message.includes('403')) {
        console.log('🔐 WebSocket 403 error - dispatching auth-expired');
        window.dispatchEvent(new Event('auth-expired'));
        setError('Authentication required');
      } else {
        setError('Failed to create WebSocket connection');
      }
      
      setMode('error');
      setLoading(false);
    }
  }, [symbol]);

  // Fallback to REST if WebSocket fails
  const fallbackToRest = useCallback(() => {
    console.log(`🔄 Falling back to REST API for ${symbol}`);
    console.log("🔍 DATA SOURCE: REST FALLBACK");
    setMode('snapshot');
    
    // Use axios instead of fetch for proper 401 handling
    api.get(`/api/v1/options/chain/${symbol}?expiry_date=${expiry}`)
      .then(response => {
        console.log('🔍 Raw API Response:', response.data);
        console.log("🔍 DATA SOURCE:", response.data.source);
        console.log("📦 REST UPDATE RECEIVED");
        
        // Extract the actual data from the response
        const actualData = response.data.data || response.data;
        console.log('📸 REST fallback data:', actualData);
        
        // Convert to WebSocket format
        const wsData: LiveMarketData = {
          symbol: actualData.symbol,
          spot: actualData.spot,
          calls: actualData.calls,
          puts: actualData.puts,
          analytics: actualData.analytics,
          intelligence: actualData.intelligence,
          timestamp: actualData.timestamp
        };
        
        setData(wsData);
        setLoading(false);
        setError(null);
      })
      .catch(err => {
        console.error('🔍 REST fallback error:', err);
        
        // Check if it's a 401 error - axios interceptor will handle redirect
        if (err.response?.status === 401) {
          console.log('🔐 401 detected in REST fallback - axios interceptor will handle redirect');
          return; // Don't set error state, let interceptor handle
        }
        
        // Only set error state if it's not a 401
        setError(err instanceof Error ? err.message : 'Unknown error occurred');
        setLoading(false);
      });
  }, [symbol, expiry]);

  // Initialize WebSocket on mount
  useEffect(() => {
    console.log(`🚀 Initializing live market data for ${symbol}`);
    
    // Start WebSocket connection
    connectWebSocket();
    
    // Set a timeout to fallback to REST if WebSocket doesn't send actual data
    const fallbackTimeout = setTimeout(() => {
      if (mode === 'loading') {
        console.log(`⏰ WebSocket timeout (no data received), falling back to REST for ${symbol}`);
        fallbackToRest();
      }
    }, 5000); // 5 seconds timeout - faster fallback
    
    return () => {
      // Cleanup
      console.log(`🧹 Cleaning up live market data for ${symbol}`);
      
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      
      if (fallbackTimeout) {
        clearTimeout(fallbackTimeout);
      }
      
      if (websocket) {
        websocket.close();
      }
    };
  }, [symbol, connectWebSocket, fallbackToRest, mode]);

  return {
    data,
    loading,
    error,
    mode,
    websocket
  };
}
