import { create } from "zustand"

interface WSStore {

  ws: WebSocket | null
  connected: boolean
  error: string | null

  spot: number
  optionChain: {
    calls: any[]
    puts: any[]
  }

  lastUpdate: number

  liveData: any
  optionChainSnapshot: any
  wsLiveData: any

  connect: (symbol: string, expiry: string) => WebSocket | null
  disconnect: () => void
  handleMessage: (message: any) => void

}

export const useWSStore = create<WSStore>((set, get) => ({

  ws: null,
  connected: false,
  error: null,

  spot: 0,
  optionChain: {
    calls: [],
    puts: []
  },

  lastUpdate: 0,

  liveData: null,
  optionChainSnapshot: null,
  wsLiveData: null,


  connect: (symbol: string, expiry: string) => {

    const existing = (window as any).__STRIKEIQ_GLOBAL_WS__

    if (existing && existing.readyState === WebSocket.OPEN) {
      console.log("WS already connected")
      return existing
    }

    console.log("Connecting WS → /ws/market")

    const ws = new WebSocket("ws://localhost:8000/ws/market")

    ;(window as any).__STRIKEIQ_GLOBAL_WS__ = ws

    ws.onopen = () => {

      console.log("WS CONNECTED")

      set({
        ws,
        connected: true,
        error: null
      })

    }

    ws.onmessage = (event) => {

      try {

        const message = JSON.parse(event.data)

        console.log("WS MESSAGE:", message)

        get().handleMessage(message)

      } catch (err) {

        console.error("WS parse error", err)

      }

    }

    ws.onclose = () => {

      console.warn("WS CLOSED")

      set({
        connected: false
      })

      setTimeout(() => {

        console.log("WS RECONNECTING")

        get().connect(symbol, expiry)

      }, 3000)

    }

    ws.onerror = (err) => {

      console.error("WS ERROR", err)

      set({
        error: "WebSocket error"
      })

    }

    set({ ws })

    return ws
  },


  disconnect: () => {

    const ws = get().ws

    if (ws) {
      ws.close()
    }

    delete (window as any).__STRIKEIQ_GLOBAL_WS__

    set({
      ws: null,
      connected: false
    })

  },


  handleMessage: (message: any) => {

    if (!message) return

    // ==========================
    // MARKET TICK
    // ==========================

    if (message.type === "market_tick" && message.data) {

      const tick = message.data

      set({

        spot: tick.ltp ?? 0,
        lastUpdate: Date.now(),

        liveData: tick,
        wsLiveData: tick

      })

      console.log("LIVE TICK RECEIVED:", tick)

      return
    }


    // ==========================
    // OPTION CHAIN UPDATE
    // ==========================

    if (message.type === "chain_update" && message.data) {

      const data = message.data

      set({

        spot: data.spot ?? 0,

        optionChain: {
          calls: data.calls ?? [],
          puts: data.puts ?? []
        },

        lastUpdate: Date.now(),

        liveData: data,
        optionChainSnapshot: data,
        wsLiveData: data

      })

      console.log("OPTION CHAIN UPDATE:", data)

      return
    }


    // ==========================
    // DIRECT OPTION CHAIN DATA
    // ==========================

    if (message.calls && message.puts) {

      set({

        spot: message.spot ?? 0,

        optionChain: {
          calls: message.calls,
          puts: message.puts
        },

        lastUpdate: Date.now(),

        liveData: message,
        optionChainSnapshot: message,
        wsLiveData: message

      })

      console.log("DIRECT OPTION CHAIN:", message)

      return
    }

  }

}))