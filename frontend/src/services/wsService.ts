import { useMarketStore } from "../stores/marketStore"
import { wsLog, wsError, wsCritical } from "@/utils/uiLogger"

let socket: WebSocket | null = null
let isConnecting = false

let reconnectAttempts = 0
let visibilityListenerAdded = false
let reconnectTimer: any = null

const MAX_RECONNECTS = 10
const WS_URL = "ws://localhost:8000/ws/market"

export function connectMarketWS() {
  wsLog("WS CONNECTING", { url: WS_URL, reconnectAttempts })

  if (reconnectAttempts > MAX_RECONNECTS) {
    wsError("WS RECONNECT LIMIT REACHED", { reconnectAttempts, maxReconnects: MAX_RECONNECTS })
    console.error("❌ Max reconnect attempts reached")
    return null
  }

  if (
    socket &&
    (socket.readyState === WebSocket.OPEN ||
     socket.readyState === WebSocket.CONNECTING)
  ) {
    console.log("🔒 WebSocket already active")
    return socket
  }

  if (
    (window as any).__strikeiq_ws &&
    (window as any).__strikeiq_ws.readyState === WebSocket.OPEN
  ) {
    console.log("🔒 Returning existing WebSocket instance")
    return (window as any).__strikeiq_ws
  }

  if (isConnecting) {
    console.log("🔒 WebSocket already connecting")
    return null
  }

  if (socket && socket.readyState === WebSocket.OPEN) {
    return socket
  }

  isConnecting = true

  // CLEAN OLD SOCKET
  if (socket) {
    socket.onopen = null
    socket.onclose = null
    socket.onmessage = null
  }

  // Close any existing WebSocket connection before creating a new one
  if ((window as any).__strikeiq_ws) {
    try {
      (window as any).__strikeiq_ws.close()
    } catch {}
  }

  socket = new WebSocket(WS_URL)

  ;(window as any).__strikeiq_ws = socket

  socket.onopen = () => {
    wsLog("WS CONNECTED", { url: WS_URL, reconnectAttempts })
    wsCritical("WS CONNECTED")

    const marketStore = useMarketStore.getState()

    marketStore.updateMarketData({
        connected: true,
        lastUpdate: Date.now()
    })

    reconnectAttempts = 0
    isConnecting = false

    if (!visibilityListenerAdded) {

      visibilityListenerAdded = true

      document.addEventListener("visibilitychange", () => {

        if (document.hidden) {

          console.log("📴 Browser tab inactive")

        } else {

          console.log("📡 Browser tab active")

        }

      })

    }

    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
    }
  }

  socket.onmessage = (event) => {
    wsLog("WS MESSAGE RECEIVED", { 
      messageType: typeof event.data,
      dataSize: event.data.length 
    })

    let data

    try {
      data =
        typeof event.data === "string"
          ? JSON.parse(event.data)
          : event.data

    } catch (e) {
      wsError("WS INVALID MESSAGE", { error: e, data: event.data })
      console.error("Invalid WS message", e)
      return
    }

    if (!data || !data.type) return

    const marketStore = useMarketStore.getState()

    // Handle different message types from backend
    switch (data.type) {
      case "index_tick":
        console.log("📈 INDEX TICK RECEIVED:", data)
        marketStore.updateIndex({
          symbol: data.symbol,
          ltp: data.data.ltp,
          change: data.data.change,
          change_percent: data.data.change_percent,
          timestamp: data.timestamp
        })
        break

      case "option_chain_update":
        console.log("📊 OPTION CHAIN UPDATE RECEIVED:", data)
        marketStore.updateOptionChain({
          symbol: data.data.symbol,
          spot: data.data.spot,
          atm_strike: data.data.atm_strike,
          expiry: data.data.expiry,
          strikes: data.data.strikes,
          timestamp: data.timestamp
        })
        break

      case "heatmap_update":
        console.log("🔥 HEATMAP UPDATE RECEIVED:", data)
        marketStore.updateHeatmap({
          symbol: data.data.symbol,
          spot: data.data.spot,
          atm_strike: data.data.atm_strike,
          pcr: data.data.pcr,
          total_call_oi: data.data.total_call_oi,
          total_put_oi: data.data.total_put_oi,
          heatmap: data.data.heatmap,
          timestamp: data.timestamp
        })
        break

      case "analytics_update":
        console.log("📈 ANALYTICS UPDATE RECEIVED:", data)
        marketStore.updateAnalytics({
          ...data.data,
          timestamp: data.timestamp
        })
        break

      case "market_status":
        console.log("🏪 MARKET STATUS RECEIVED:", data)
        marketStore.setMarketOpen(data.data.market_open)
        break

      // Legacy message types for backward compatibility
      case "spot_tick":
        console.log("📍 LEGACY SPOT TICK RECEIVED:", data)
        marketStore.setSpot(data.spot)
        break

      case "market_data":
        console.log("📊 LEGACY MARKET DATA RECEIVED:", data)
        if (data.spot !== undefined) {
          marketStore.setSpot(data.spot)
        }
        break

      case "option_chain":
        console.log("📊 LEGACY OPTION CHAIN RECEIVED:", data)
        marketStore.updateOptionChain({
          symbol: data.chain.symbol,
          spot: data.chain.spot,
          atm_strike: data.chain.atm_strike,
          expiry: data.chain.expiry,
          strikes: data.chain.strikes,
          timestamp: Date.now()
        })
        break

      case "ai_signal":
        console.log("🤖 LEGACY AI SIGNAL RECEIVED:", data)
        marketStore.setAISignals(data.signals || [])
        break

      default:
        console.warn("🤔 UNKNOWN MESSAGE TYPE:", data.type, data)
        break
    }
  }

  socket.onclose = (event) => {
    wsLog("WS CLOSED", { 
      code: event.code,
      reason: event.reason,
      reconnectAttempts 
    })
    wsCritical("WS DISCONNECTED")

    const marketStore = useMarketStore.getState()

    marketStore.updateMarketData({
        connected: false,
        marketOpen: false,
        lastUpdate: Date.now()
    })

    scheduleReconnect()
  }

  socket.onerror = (err) => {
    wsError("WS ERROR", { 
      error: err,
      readyState: socket?.readyState,
      url: WS_URL 
    })

    console.error("WebSocket error", err)

    if (socket) {
      console.error("Socket readyState:", socket.readyState)
    }
  }

  return socket
}

function scheduleReconnect() {
  if (reconnectAttempts >= MAX_RECONNECTS) {
    wsError("WS RECONNECT LIMIT REACHED", { reconnectAttempts, maxReconnects: MAX_RECONNECTS })
    console.error("❌ Max reconnect attempts reached")
    return
  }

  reconnectAttempts++
  const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000) // Exponential backoff, max 30s

  wsLog("WS SCHEDULING RECONNECT", { 
    attempt: reconnectAttempts, 
    delay,
    maxDelay: 30000 
  })

  reconnectTimer = setTimeout(() => {
    console.log(`🔄 Reconnecting... Attempt ${reconnectAttempts}/${MAX_RECONNECTS}`)
    connectMarketWS()
  }, delay)
}

export function disconnectMarketWS() {
  if (socket) {
    socket.close()
    socket = null
  }

  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }

  const marketStore = useMarketStore.getState()
  marketStore.updateMarketData({
    connected: false,
    lastUpdate: Date.now()
  })
}

export function getWSConnectionStatus() {
  return {
    connected: socket?.readyState === WebSocket.OPEN,
    connecting: isConnecting,
    reconnectAttempts,
    url: WS_URL
  }
}
