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

import { create } from 'zustand';

interface WSStore {
  ws: WebSocket | null;
  isConnected: boolean;
  isInitializing: boolean;
  lastMessage: any;
  error: string | null;
  reconnectAttempts: number;
  maxReconnectAttempts: number;
  
  // Actions
  setWS: (ws: WebSocket | null) => void;
  setConnected: (connected: boolean) => void;
  setInitializing: (initializing: boolean) => void;
  setLastMessage: (message: any) => void;
  setError: (error: string | null) => void;
  incrementReconnectAttempts: () => void;
  resetReconnectAttempts: () => void;
}

export const useWSStore = create<WSStore>((set) => ({
  ws: null,
  isConnected: false,
  isInitializing: false,
  lastMessage: null,
  error: null,
  reconnectAttempts: 0,
  maxReconnectAttempts: 5,
  
  setWS: (ws) => set({ ws }),
  setConnected: (isConnected) => set({ isConnected }),
  setInitializing: (isInitializing) => set({ isInitializing }),
  setLastMessage: (lastMessage) => set({ lastMessage }),
  setError: (error) => set({ error }),
  incrementReconnectAttempts: () => set((state) => ({ 
    reconnectAttempts: state.reconnectAttempts + 1 
  })),
  resetReconnectAttempts: () => set({ reconnectAttempts: 0 }),
}));
