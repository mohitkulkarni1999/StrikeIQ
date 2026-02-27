import { create } from "zustand"

interface WSStore {

ws: WebSocket | null
connected: boolean
error: string | null
isInitializing: boolean

// ===== STATUS INDICATORS =====

marketOpen: boolean
marketStatus: string
wsHeartbeat: boolean

spot: number

optionChain: {
calls: any[]
puts: any[]
}

lastUpdate: number

liveData: any
optionChainSnapshot: any
wsLiveData: any
lastMessage: any
marketData: any

reconnectAttempts: number
maxReconnectAttempts: number

connect: (symbol: string, expiry: string) => WebSocket | null
disconnect: () => void
handleMessage: (message: any) => void

setWS: (ws: WebSocket | null) => void
setConnected: (connected: boolean) => void
setError: (error: string | null) => void
setInitializing: (isInitializing: boolean) => void
setLastMessage: (message: any) => void
setMarketData: (data: any) => void

setMarketOpen: (status: boolean) => void
setMarketStatus: (status: string) => void
setHeartbeat: (status: boolean) => void

incrementReconnectAttempts: () => void
resetReconnectAttempts: () => void
}

export const useWSStore = create<WSStore>((set, get) => ({

ws: null,
connected: false,
error: null,
isInitializing: false,

marketOpen: false,
marketStatus: "CLOSED",
wsHeartbeat: false,

spot: 0,

optionChain: {
calls: [],
puts: []
},

lastUpdate: 0,

liveData: null,
optionChainSnapshot: null,
wsLiveData: null,
lastMessage: null,
marketData: null,

reconnectAttempts: 0,
maxReconnectAttempts: 5,

// ================================
// CONNECT WEBSOCKET
// ================================

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

  console.log("🟢 WS CONNECTED")

  set({
    ws,
    connected: true,
    error: null
  })

  get().resetReconnectAttempts()

}

ws.onmessage = (event) => {

  try {

    const message = JSON.parse(event.data)

    get().setLastMessage(message)

    get().handleMessage(message)

  } catch (err) {

    console.error("WS parse error", err)

  }

}

ws.onclose = () => {

  console.warn("🔴 WS CLOSED")

  set({
    connected: false,
    wsHeartbeat: false
  })

  get().incrementReconnectAttempts()

  if (get().reconnectAttempts <= get().maxReconnectAttempts) {

    setTimeout(() => {

      console.log("WS RECONNECTING")

      get().connect(symbol, expiry)

    }, 3000)

  }

}

ws.onerror = () => {

  console.error("WS ERROR")

  set({
    error: "WebSocket error"
  })

}

set({ ws })

return ws

},

// ================================
// DISCONNECT
// ================================

disconnect: () => {
const ws = get().ws

if (ws) {
  ws.close()
}

delete (window as any).__STRIKEIQ_GLOBAL_WS__

set({
  ws: null,
  connected: false,
  wsHeartbeat: false
})

},

// ================================
// MESSAGE HANDLER
// ================================

handleMessage: (message: any) => {
if (!message) return

// ================================
// HEARTBEAT (ping)
// ================================

if (message.type === "ping") {

  set({
    wsHeartbeat: true
  })

  // reset heartbeat after 10s
  setTimeout(() => {

    set({
      wsHeartbeat: false
    })

  }, 10000)

  return
}


// ================================
// MARKET TICK
// ================================

if (message.type === "market_tick" && message.data) {

  const tick = message.data

  set({

    spot: tick.ltp ?? 0,

    lastUpdate: Date.now(),

    liveData: tick,
    wsLiveData: tick

  })

  console.log("📈 LIVE TICK:", tick)

  return
}


// ================================
// OPTION CHAIN UPDATE
// ================================

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

  console.log("📊 OPTION CHAIN UPDATE")

  return
}


// ================================
// DIRECT OPTION CHAIN DATA
// ================================

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

  console.log("📊 DIRECT OPTION CHAIN")

  return
}

},

// ================================
// SETTERS
// ================================

setWS: (ws) => set({ ws }),
setConnected: (connected) => set({ connected }),
setError: (error) => set({ error }),
setInitializing: (isInitializing) => set({ isInitializing }),
setLastMessage: (message) => set({ lastMessage: message }),
setMarketData: (data) => set({ marketData: data }),

setMarketOpen: (status) => set({ marketOpen: status }),
setMarketStatus: (status) => set({ marketStatus: status }),
setHeartbeat: (status) => set({ wsHeartbeat: status }),

incrementReconnectAttempts: () =>
set((state) => ({
reconnectAttempts: state.reconnectAttempts + 1
})),

resetReconnectAttempts: () =>
set({
reconnectAttempts: 0
})

}))
