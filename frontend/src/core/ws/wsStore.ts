/**
 * WebSocket Zustand Store - READ ONLY
 * 
 * This store reads WebSocket state from the singleton service.
 * All components must read from this store.
 */

import { create } from "zustand"
import { uiLog } from "@/utils/uiLogger"

interface WSStore {
  connected: boolean
  marketOpen: boolean | null
  lastMessage: any | null
  error: string | null
  spot: number
  lastUpdate: number
  marketData: any
  optionChainSnapshot: any
  liveData: any
  wsLiveData: any
  _lastChainUpdate: number
  _THROTTLE_MS: number
  handleMessage: (message: any) => void
  setConnected: (v: boolean) => void
  setMarketOpen: (v: boolean | null) => void
  setLastMessage: (msg: any) => void
  setMarketData: (data: any) => void
  setError: (error: string | null) => void
}

export const useWSStore = create<WSStore>((set, get) => ({

  connected: false,
  marketOpen: null,
  lastMessage: null,
  error: null,
  spot: 0,
  marketData: null,
  optionChainSnapshot: null,
  liveData: null,
  wsLiveData: null,
  lastUpdate: 0,
  _lastChainUpdate: 0,
  _THROTTLE_MS: 50,

  handleMessage: (message: any) => {
    if (!message) return

    // Market status update
    if (message.type === "market_status" && message.market_open !== undefined) {
      console.log("📊 STORE: market_status →", message.market_open)
      set({ marketOpen: message.market_open, error: null })
      return
    }

    // Market tick
    if (message.type === "market_tick" && message.data) {
      const tick = message.data
      console.log("📊 STORE: market_tick → LTP=", tick.ltp)
      set({
        spot: tick.ltp ?? 0,
        lastUpdate: Date.now(),
        liveData: tick,
        wsLiveData: tick,
        error: null
      })
      return
    }

    // Market data with spot price
    if (message.type === "market_data" && message.spot !== undefined) {
      console.log("📊 STORE: market_data → spot=", message.spot)
      set({
        spot: message.spot,
        lastUpdate: Date.now(),
        marketData: message,
        liveData: message,
        wsLiveData: message,
        error: null
      })
      return
    }

    // Market data with direct ltp (fallback)
    if (message.type === "market_data" && message.ltp !== undefined) {
      console.log("📊 STORE: market_data → LTP=", message.ltp)
      set({
        spot: message.ltp,
        lastUpdate: Date.now(),
        liveData: message,
        wsLiveData: message,
        error: null
      })
      return
    }

    // Chain update
    if (message.type === "chain_update" && message.data) {
      const now = Date.now()
      const store = get()

      if (now - store._lastChainUpdate < store._THROTTLE_MS) {
        return
      }

      const data = message.data
      console.log("📊 STORE: chain_update → spot=", data.spot)
      set({
        spot: data.spot ?? 0,
        marketData: data,
        optionChainSnapshot: data,
        lastUpdate: now,
        _lastChainUpdate: now,
        error: null
      })
      return
    }

    // Raw option chain
    if (message.calls && message.puts) {
      const now = Date.now()
      const store = get()

      if (now - store._lastChainUpdate < store._THROTTLE_MS) {
        return
      }

      console.log("📊 STORE: optionChain → spot=", message.spot)
      set({
        spot: message.spot ?? 0,
        marketData: message,
        optionChainSnapshot: message,
        lastUpdate: now,
        _lastChainUpdate: now,
        error: null
      })
      return
    }

    console.warn("⚠️ WS UNKNOWN MESSAGE TYPE:", message.type)
    set({ error: `Unknown message type: ${message.type}` })
  },

  setConnected: (v) => {
    uiLog("STORE UPDATE", { 
      store: "wsStore", 
      action: "setConnected", 
      connected: v 
    })
    set({ connected: v })
  },
  setMarketOpen: (v) => {
    uiLog("STORE UPDATE", { 
      store: "wsStore", 
      action: "setMarketOpen", 
      marketOpen: v 
    })
    set({ marketOpen: v })
  },
  setLastMessage: (msg) => {
    uiLog("STORE UPDATE", { 
      store: "wsStore", 
      action: "setLastMessage", 
      messageType: msg?.type 
    })
    set({ lastMessage: msg })
  },
  setMarketData: (data) => {
    uiLog("STORE UPDATE", { 
      store: "wsStore", 
      action: "setMarketData", 
      spot: data?.spot,
      symbol: data?.symbol 
    })
    set({ marketData: data })
  },
  setError: (error) => {
    uiLog("STORE UPDATE", { 
      store: "wsStore", 
      action: "setError", 
      error 
    })
    set({ error })
  }
}))
