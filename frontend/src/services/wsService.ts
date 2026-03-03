import { useMarketStore } from "../stores/marketStore"
import { useWSStore } from "../core/ws/wsStore"

let socket: WebSocket | null = null
let isConnecting = false

let reconnectAttempts = 0
let visibilityListenerAdded = false
let reconnectTimer: any = null

const MAX_RECONNECTS = 5
const WS_URL = "ws://localhost:8000/ws/market"

export function connectMarketWS() {

  if (
    (window as any).STRIKEIQ_WS_INSTANCE &&
    (window as any).STRIKEIQ_WS_INSTANCE.readyState === WebSocket.OPEN
  ) {
    console.log("🔒 Returning existing WebSocket instance")
    return (window as any).STRIKEIQ_WS_INSTANCE
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

  socket = new WebSocket(WS_URL)

  ;(window as any).STRIKEIQ_WS_INSTANCE = socket

  socket.onopen = () => {

    console.log("✅ WebSocket connected")

    const store = useWSStore.getState()

    store.setConnected(true)

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

  let data

  try {
    data = JSON.parse(event.data)
  } catch {
    return
  }

  const store = useWSStore.getState()

  if (data.type === "market_status") {

    console.log("📊 WS MARKET STATUS:", data.market_open)

    store.setMarketOpen(data.market_open)
    store.setConnected(true)

    return
  }

  if (data.type === "market_data") {

    console.log("📡 WS MARKET DATA RECEIVED")

    // Handle spot price updates
    if (data.spot !== undefined) {
      const marketStore = useMarketStore.getState()
      marketStore.setSpot(data.spot)
      console.log("📍 SPOT UPDATED:", data.spot)
    }

    store.setMarketData(data)
    store.setConnected(true)

    return
  }

  if (data.type === "option_chain") {

    console.log("📡 WS OPTION CHAIN RECEIVED")

    const marketStore = useMarketStore.getState()
    marketStore.setOptionChain(data.chain)
    store.setConnected(true)

    return
  }

  if (data.type === "ai_signal") {

    console.log("🤖 WS AI SIGNAL RECEIVED:", data.signals)

    const marketStore = useMarketStore.getState()
    marketStore.setAISignals(data.signals || [])
    store.setConnected(true)

    return
  }

}

  socket.onclose = () => {

  console.log("❌ WebSocket closed")

  const store = useWSStore.getState()

  store.setConnected(false)

}

  socket.onerror = (err) => {

    console.error("WebSocket error", err)

    if (socket) {
      console.error("Socket readyState:", socket.readyState)
    }

  }

  return socket
}

function scheduleReconnect() {

  if (reconnectAttempts >= MAX_RECONNECTS) {
    console.error("❌ Max reconnect attempts reached")
    return
  }

  const delay = 1000 * Math.pow(2, reconnectAttempts)

  reconnectTimer = setTimeout(() => {

    reconnectAttempts++

    console.log("🔄 Reconnecting WebSocket attempt", reconnectAttempts)

    connectMarketWS()

  }, delay)
}
