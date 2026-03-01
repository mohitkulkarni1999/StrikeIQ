import { create } from "zustand";

interface OptionChainStore {
  optionChainWs: WebSocket | null;
  optionChainConnected: boolean;
  optionChainError: string | null;
  optionChainData: any;
  optionChainLastUpdate: number;

  connectOptionChain: (symbol: string, expiry: string) => WebSocket | null;
  disconnectOptionChain: () => void;
  setOptionChainWs: (ws: WebSocket | null) => void;
  setOptionChainConnected: (connected: boolean) => void;
  setOptionChainError: (error: string | null) => void;
  setOptionChainData: (data: any) => void;
}

export const useOptionChainStore = create<OptionChainStore>((set, get) => ({
  optionChainWs: null,
  optionChainConnected: false,
  optionChainError: null,
  optionChainData: null,
  optionChainLastUpdate: 0,

  connectOptionChain: (symbol: string, expiry: string) => {
    const existing = (window as any).__STRIKEIQ_OPTION_CHAIN_WS__;

    if (existing && existing.readyState === WebSocket.OPEN) {
      console.log("Option Chain WS already connected");
      return existing;
    }

    console.log(`Connecting Option Chain WS → /ws/live-options/${symbol}?expiry=${expiry}`);

    const ws = new WebSocket(`ws://localhost:8000/ws/live-options/${symbol}?expiry=${expiry}`);

    (window as any).__STRIKEIQ_OPTION_CHAIN_WS__ = ws;

    ws.onopen = () => {
      console.log("🟢 OPTION CHAIN WS CONNECTED");
      set({
        optionChainWs: ws,
        optionChainConnected: true,
        optionChainError: null
      });
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        if (message.type === "chain_update" && message.data) {
          const data = message.data;
          
          set({
            optionChainData: data,
            optionChainLastUpdate: Date.now()
          });

          console.log("📊 OPTION CHAIN UPDATE:", data.symbol, data.expiry);
        }
      } catch (err) {
        console.error("Option Chain WS parse error", err);
      }
    };

    ws.onclose = () => {
      console.warn("🔴 OPTION CHAIN WS CLOSED");
      set({
        optionChainConnected: false,
        optionChainWs: null
      });

      delete (window as any).__STRIKEIQ_OPTION_CHAIN_WS__;
    };

    ws.onerror = (error) => {
      console.error("OPTION CHAIN WS ERROR", error);
      set({
        optionChainError: "Option Chain WebSocket error"
      });
    };

    set({ optionChainWs: ws });
    return ws;
  },

  disconnectOptionChain: () => {
    const ws = get().optionChainWs;

    if (ws) {
      ws.close();
    }

    delete (window as any).__STRIKEIQ_OPTION_CHAIN_WS__;

    set({
      optionChainWs: null,
      optionChainConnected: false,
      optionChainData: null,
      optionChainError: null
    });
  },

  setOptionChainWs: (ws) => set({ optionChainWs: ws }),
  setOptionChainConnected: (connected) => set({ optionChainConnected: connected }),
  setOptionChainError: (error) => set({ optionChainError: error }),
  setOptionChainData: (data) => set({ optionChainData: data, optionChainLastUpdate: Date.now() })
}));
