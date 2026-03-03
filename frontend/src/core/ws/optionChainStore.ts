/**
 * Option Chain Store
 * 
 * ARCHITECTURE: This store does NOT create WebSocket connections.
 * It receives option chain data from the canonical wsStore
 * which is fed by wsService.ts singleton.
 * 
 * The data flow for option chain is:
 *   Backend live_ws.py → ws/live-options/{symbol} endpoint
 *   → wsService.ts onmessage → wsStore.handleMessage
 *   → chain_update → this store via subscription
 */

import { create } from "zustand";
import { useWSStore } from "./wsStore";

interface OptionChainStore {
  optionChainConnected: boolean;
  optionChainError: string | null;
  optionChainData: any;
  optionChainLastUpdate: number;

  setOptionChainConnected: (connected: boolean) => void;
  setOptionChainError: (error: string | null) => void;
  setOptionChainData: (data: any) => void;
}

export const useOptionChainStore = create<OptionChainStore>((set, get) => ({
  optionChainConnected: false,
  optionChainError: null,
  optionChainData: null,
  optionChainLastUpdate: 0,

  setOptionChainConnected: (connected) => set({ optionChainConnected: connected }),
  setOptionChainError: (error) => set({ optionChainError: error }),
  setOptionChainData: (data) => set({ optionChainData: data, optionChainLastUpdate: Date.now() })
}));

// ============================================================
// SUBSCRIBE to wsStore for chain_update messages
// This bridges chain data from the singleton WS to this store.
// ============================================================
if (typeof window !== "undefined") {
  useWSStore.subscribe((state, prevState) => {
    // When optionChainSnapshot changes in wsStore, sync to this store
    if (state.optionChainSnapshot !== prevState.optionChainSnapshot && state.optionChainSnapshot) {
      useOptionChainStore.getState().setOptionChainData(state.optionChainSnapshot);
      useOptionChainStore.getState().setOptionChainConnected(true);
    }

    // Sync connected state
    if (state.connected !== prevState.connected) {
      useOptionChainStore.getState().setOptionChainConnected(state.connected);
    }
  });
}
