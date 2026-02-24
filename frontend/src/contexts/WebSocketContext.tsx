import React, { createContext, useContext, useEffect, useRef, useState, ReactNode } from 'react';

interface WebSocketContextType {
  ws: WebSocket | null;
  isConnected: boolean;
  connect: (symbol: string, expiry: string) => Promise<void>;
  disconnect: () => void;
  lastMessage: any;
  error: string | null;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

interface WebSocketProviderProps {
  children: ReactNode;
}

export function WebSocketProvider({ children }: WebSocketProviderProps) {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 3000; // 3 seconds

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (ws) {
      ws.close();
      setWs(null);
    }
    setIsConnected(false);
    reconnectAttemptsRef.current = 0;
  };

  const connect = async (symbol: string, expiry: string) => {
    try {
      // First call the WebSocket init API
      console.log('Initializing WebSocket connection...');
      const response = await fetch('/api/ws/init', {
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error(`WebSocket init failed: ${response.status}`);
      }

      console.log('WebSocket init successful, connecting to WebSocket...');

      // Close existing connection if any
      disconnect();

      // Create WebSocket connection
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsHost = window.location.hostname;
      const wsUrl = `${wsProtocol}//${wsHost}:8000/ws/live-options/${symbol}?expiry=${encodeURIComponent(expiry)}`;
      const websocket = new WebSocket(wsUrl);

      websocket.onopen = () => {
        console.log('WebSocket connected successfully');
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
      };

      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket message received:', data);
          setLastMessage(data);
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      websocket.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setIsConnected(false);
        setWs(null);

        // Attempt reconnection if not manually closed and under max attempts
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          console.log(`Attempting to reconnect in ${reconnectDelay}ms (attempt ${reconnectAttemptsRef.current})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            connect(symbol, expiry);
          }, reconnectDelay);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          setError('Max reconnection attempts reached. Please refresh the page.');
        }
      };

      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('WebSocket connection error');
      };

      setWs(websocket);

    } catch (err) {
      console.error('Failed to connect WebSocket:', err);
      setError(err instanceof Error ? err.message : 'Failed to connect WebSocket');
    }
  };

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, []);

  const value: WebSocketContextType = {
    ws,
    isConnected,
    connect,
    disconnect,
    lastMessage,
    error
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
}
