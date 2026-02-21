import { useState, useEffect, useRef, useCallback, useMemo } from 'react';

// Types for optimized WebSocket
interface OptimizedWebSocketMessage {
  type: 'market_update' | 'signal' | 'error' | 'connected' | 'disconnected';
  timestamp: string;
  data?: any;
  error?: string;
}

interface OptimizedWebSocketState {
  isConnected: boolean;
  lastUpdate: string | null;
  marketData: any;
  signals: any[];
  error: string | null;
  connectionAttempts: number;
}

interface UseOptimizedWebSocketReturn {
  state: OptimizedWebSocketState;
  sendMessage: (message: any) => void;
  reconnect: () => void;
  connectionQuality: 'excellent' | 'good' | 'poor' | 'disconnected';
}

/**
 * Optimized WebSocket hook with state isolation and performance tracking
 * Prevents unnecessary re-renders and provides stable state management
 */
export function useOptimizedWebSocket(url: string): UseOptimizedWebSocketReturn {
  // Use refs for WebSocket instance to prevent re-creation
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef<boolean>(true);
  
  // State management with proper isolation
  const [state, setState] = useState<OptimizedWebSocketState>({
    isConnected: false,
    lastUpdate: null,
    marketData: null,
    signals: [],
    error: null,
    connectionAttempts: 0
  });
  
  // Memoized state setters to prevent unnecessary re-renders
  const updateState = useCallback((updates: Partial<OptimizedWebSocketState>) => {
    setState(prev => {
      const newState = { ...prev, ...updates };
      
      // Log state changes for debugging
      if (process.env.NODE_ENV === 'development') {
        console.log('🔄 WebSocket State Update:', {
          from: prev,
          to: newState,
          changes: updates
        });
      }
      
      return newState;
    });
  }, []);
  
  // Connection logic
  const connect = useCallback(() => {
    if (!mountedRef.current) return;
    
    try {
      setState((prev: OptimizedWebSocketState) => ({
        ...prev,
        error: null,
        connectionAttempts: prev.connectionAttempts + 1
      }));
      
      const ws = new WebSocket(url);
      wsRef.current = ws;
      
      ws.onopen = () => {
        if (!mountedRef.current) return;
        
        console.log('✅ Optimized WebSocket connected');
        updateState({
          isConnected: true,
          error: null,
          lastUpdate: new Date().toISOString()
        });
        
        // Clear any pending reconnect timeout
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };
      
      ws.onmessage = (event) => {
        if (!mountedRef.current) return;
        
        try {
          const message: OptimizedWebSocketMessage = JSON.parse(event.data);
          
          // Handle different message types
          switch (message.type) {
            case 'market_update':
              // Only update market data if it's actually different
              setState(prev => {
                const marketDataChanged = JSON.stringify(prev.marketData) !== JSON.stringify(message.data);
                
                if (marketDataChanged) {
                  return {
                    ...prev,
                    marketData: message.data,
                    lastUpdate: message.timestamp
                  };
                }
                return prev;
              });
              break;
              
            case 'signal':
              // Append new signals without replacing existing ones
              setState(prev => ({
                ...prev,
                signals: [...prev.signals, message.data].slice(-100), // Keep last 100 signals
                lastUpdate: message.timestamp
              }));
              break;
              
            case 'connected':
              setState(prev => ({
                ...prev,
                isConnected: true,
                error: null,
                lastUpdate: message.timestamp
              }));
              break;
              
            case 'error':
              setState(prev => ({
                ...prev,
                error: message.error || 'Unknown WebSocket error',
                lastUpdate: message.timestamp
              }));
              break;
              
            default:
              console.log('📡 Unknown message type:', message.type);
          }
        } catch (error) {
          console.error('❌ Failed to parse WebSocket message:', error);
          setState(prev => ({
            ...prev,
            error: 'Failed to parse message'
          }));
        }
      };
      
      ws.onclose = (event) => {
        if (!mountedRef.current) return;
        
        console.log(`🔌 WebSocket closed: ${event.code} - ${event.reason}`);
        
        setState(prev => ({
          ...prev,
          isConnected: false,
          error: event.code !== 1000 ? `Connection closed (${event.code})` : null
        }));
        
        // Auto-reconnect with exponential backoff
        if (event.code !== 1000) { // Not a normal closure
          const delay = Math.min(30000, 1000 * Math.pow(2, state.connectionAttempts));
          
          reconnectTimeoutRef.current = setTimeout(() => {
            if (mountedRef.current) {
              connect();
            }
          }, delay);
        }
      };
      
      ws.onerror = (error) => {
        if (!mountedRef.current) return;
        
        console.error('❌ WebSocket error:', error);
        updateState({
          error: 'WebSocket connection error',
          isConnected: false
        });
      };
      
    } catch (error) {
      console.error('❌ Failed to create WebSocket:', error);
      updateState({ error: 'Failed to create WebSocket connection' });
    }
  }, [url, state.connectionAttempts, updateState]);
  
  // Memoized send message function
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify(message));
      } catch (error) {
        console.error('❌ Failed to send WebSocket message:', error);
        setState(prev => ({
          ...prev,
          error: 'Failed to send message'
        }));
      }
    } else {
      console.warn('⚠️ WebSocket not ready, cannot send message');
    }
  }, [setState]);
  
  // Memoized reconnect function
  const reconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setState(prev => ({
      ...prev,
      connectionAttempts: prev.connectionAttempts + 1
    }));
    
    connect();
  }, [setState, connect]);
  
  // Calculate connection quality based on state
  const connectionQuality = useMemo(() => {
    if (state.isConnected) {
      return state.error ? 'poor' : 'excellent';
    } else if (state.error) {
      return 'poor';
    } else {
      return 'disconnected';
    }
  }, [state.isConnected, state.error]);
  
  // Initial connection
  useEffect(() => {
    connect();
    
    // Cleanup
    return () => {
      mountedRef.current = false;
      
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [url, connect]);
  
  return {
    state,
    sendMessage,
    reconnect,
    connectionQuality
  };
}

/**
 * Hook for managing market data with debounced updates
 * Prevents excessive re-renders from high-frequency updates
 */
export function useDebouncedMarketData(websocketState: OptimizedWebSocketState, debounceMs: number = 100) {
  const [debouncedData, setDebouncedData] = useState<any>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  useEffect(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    timeoutRef.current = setTimeout(() => {
      setDebouncedData(websocketState.marketData);
    }, debounceMs);
    
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [websocketState.marketData, debounceMs]);
  
  return debouncedData;
}

/**
 * Hook for managing signals with filtering and deduplication
 */
export function useFilteredSignals(signals: any[], maxAgeMs: number = 60000) {
  const filteredSignals = useMemo(() => {
    const now = Date.now();
    const cutoffTime = now - maxAgeMs;
    
    // Filter by age and deduplicate
    const uniqueSignals = new Map();
    
    signals
      .filter(signal => {
        const signalTimestamp = new Date(signal.timestamp).getTime();
        return signalTimestamp > cutoffTime;
      })
      .forEach(signal => {
        const signalTime = new Date(signal.timestamp).getTime();
        const key = `${signal.type}-${signal.instrument}-${Math.floor(signalTime / 10000)}`; // 10-second buckets
        if (!uniqueSignals.has(key)) {
          uniqueSignals.set(key, signal);
        }
      });
    
    return Array.from(uniqueSignals.values());
  }, [signals, maxAgeMs]);
  
  return filteredSignals;
}
