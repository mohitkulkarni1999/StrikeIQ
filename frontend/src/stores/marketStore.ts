import { create } from 'zustand';
import { storeLogger, traceManager } from '../utils/logger';

interface MarketData {
  [key: string]: any;
}

interface MarketStore {
  connected: boolean;
  marketOpen: boolean | null;
  data: MarketData | null;
  lastUpdate: string | null;
  currentSymbol: string;
  spot: number | null;
  optionChain: any;
  aiSignals: any[];
  setConnected: (connected: boolean) => void;
  setMarketOpen: (open: boolean) => void;
  setCurrentSymbol: (symbol: string) => void;
  setSpot: (spot: number) => void;
  setOptionChain: (chain: any) => void;
  setAISignals: (signals: any[]) => void;
  updateMarketData: (data: Partial<MarketData> & { connected: boolean; marketOpen: boolean; lastUpdate: string }) => void;
}

export const useMarketStore = create<MarketStore>((set) => ({
  connected: false,
  marketOpen: null,
  data: null,
  lastUpdate: null,
  currentSymbol: 'NIFTY', // Default symbol
  spot: null,
  optionChain: {},
  aiSignals: [],
  
  setConnected: (connected: boolean) => {
    const traceId = traceManager.getTraceId();
    storeLogger.info("STORE UPDATE", { traceId, field: "connected", value: connected });
    
    set({ connected });
  },
  
  setMarketOpen: (open: boolean) => {
    const traceId = traceManager.getTraceId();
    storeLogger.info("STORE UPDATE", { traceId, field: "marketOpen", value: open });
    
    set({ marketOpen: open });
  },
  
  setCurrentSymbol: (symbol: string) => {
    const traceId = traceManager.getTraceId();
    storeLogger.info("STORE UPDATE", { traceId, field: "currentSymbol", value: symbol });
    
    set({ currentSymbol: symbol });
  },
  
  setSpot: (spot: number) => {
    const traceId = traceManager.getTraceId();
    storeLogger.info("STORE UPDATE", { traceId, field: "spot", value: spot });
    
    set({ spot });
  },
  
  setOptionChain: (chain: any) => {
    const traceId = traceManager.getTraceId();
    storeLogger.info("STORE UPDATE", { traceId, field: "optionChain", size: Object.keys(chain).length });
    
    set({ optionChain: chain });
  },
  
  setAISignals: (signals: any[]) => {
    const traceId = traceManager.getTraceId();
    storeLogger.info("STORE UPDATE", { traceId, field: "aiSignals", count: signals.length });
    
    set({ aiSignals: signals });
  },
  
  updateMarketData: (update) => {
    const traceId = traceManager.getTraceId();
    storeLogger.info("STORE UPDATE", { traceId, field: "marketData", update });
    
    set((state) => ({
      ...state,
      ...update
    }));
  },
}));
